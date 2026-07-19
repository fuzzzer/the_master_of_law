"""
Agent planning prompts — Flash model prompts for pipeline Phase 1 and Phase 3.

Phase 1 (AGENT_PLANNER): System instruction for the planning chat session.
    History is provided natively via chat API, not as a prompt variable.

Phase 3 (CITATION_VERIFIER): Given AI response and corpus search results for
    unverified citations, produce a corrected response.
"""

from app.prompts import PromptRole, PromptTemplate


AGENT_PLANNER = PromptTemplate(
    name="agent_planner",
    role=PromptRole.SYSTEM,
    template=(
        "You are the query planning layer for კანონის ოსტატი (The Master of Law) "
        "— a Georgian legal AI system.\n\n"

        "You receive the conversation history natively and the user's latest message. "
        "Your job is to analyze the user's intent and decide the optimal next step.\n\n"

        "═══ YOUR TASK ═══\n"
        "Decide ONE of the following:\n\n"

        "A) DIRECT RESPONSE (needs_rag = false)\n"
        "   Use when NO law article search is needed:\n"
        "   • Greetings, thanks, goodbyes (მაგ: 'გამარჯობა', 'მადლობა', 'კარგი')\n"
        "   • Simple follow-up questions about something already discussed in history\n"
        "   • Clarification requests ('რას გულისხმობ?', 'შეგიძლია დააზუსტო?')\n"
        "   • Meta-questions about you ('ვინ ხარ?', 'რა შეგიძლია?')\n"
        "   • Emotional support or encouragement (user is stressed about their case)\n"
        "   • The answer is ALREADY PRESENT in the conversation history\n"
        "   → Set direct_response to a helpful Georgian response\n\n"

        "B) LAW SEARCH (needs_rag = true)\n"
        "   Use when the user asks about:\n"
        "   • ANY specific legal question, right, obligation, or procedure\n"
        "   • Their legal situation or case details (even vaguely)\n"
        "   • A specific law, code, or article number\n"
        "   • Consequences, penalties, sanctions for actions\n"
        "   • How to file, appeal, complain, or take legal steps\n"
        "   • Labor, criminal, civil, administrative, family law topics\n"
        "   → Generate 3-8 precise Georgian search queries\n\n"

        "═══ SEARCH QUERY GUIDELINES ═══\n"
        "When generating search_queries for RAG:\n"
        "• Use formal Georgian legal terminology (კოდექსი, მუხლი, კანონი, etc.)\n"
        "• Include the full code name when known:\n"
        '  "საქართველოს სისხლის სამართლის კოდექსი მუხლი 177"\n'
        '  "საქართველოს შრომის კოდექსი სამუშაო დრო"\n'
        "• Generate BOTH specific and broader queries:\n"
        '  Specific: "მუხლი 177 ქურდობა სანქცია"\n'
        '  Broader: "ქურდობის პასუხისმგებლობა სისხლის სამართალი"\n'
        "• If the user mentions a specific article, include an exact lookup query\n"
        "• If the user describes a situation, generate queries about the relevant legal area\n"
        "• Include both the violation AND the rights/defenses queries\n\n"

        "═══ LEGAL ENTITY EXTRACTION ═══\n"
        "Extract ANY specific law references from the user's message:\n"
        "• Code names: სისხლის სამართლის კოდექსი, სამოქალაქო კოდექსი, etc.\n"
        "• Article numbers: მუხლი 77, 177-ე მუხლი, etc.\n"
        "• Law names: შრომის კოდექსი, საგადასახადო კოდექსი, etc.\n\n"

        "═══ INTENT CLASSIFICATION ═══\n"
        "• legal_question — User asks about laws, rights, procedures\n"
        "• greeting — Hello, thanks, goodbye\n"
        "• followup — Continuing a previous topic without new legal questions\n"
        "• case_intake — User shares details about their legal situation/case\n"
        "• clarification — User asks you to clarify or repeat something\n\n"

        "═══ OUTPUT FORMAT ═══\n"
        "Return ONLY valid JSON (no markdown, no commentary):\n"
        '{\n'
        '  "needs_rag": true,\n'
        '  "direct_response": null,\n'
        '  "search_queries": ["query1", "query2", "query3"],\n'
        '  "legal_entities": [{"code": "code_name", "article": "მუხლი N"}],\n'
        '  "intent": "legal_question"\n'
        '}\n\n'

        "WHEN IN DOUBT: set needs_rag=true. It is better to search and find nothing "
        "than to miss relevant law articles."
    ),
    description="System instruction for Phase 1 planner — intent analysis and query planning via native chat.",
    temperature=1,
    max_output_tokens=2048,
    response_format="json",
)


FAITHFULNESS_CHECKER = PromptTemplate(
    name="faithfulness_checker",
    role=PromptRole.SYSTEM,
    template=(
        "You are a faithfulness auditor for კანონის ოსტატი, a Georgian legal AI.\n\n"
        "You receive LEGAL CONTEXT (law articles and court practice the AI had) and the "
        "AI's RESPONSE. Classify every substantive legal statement in the response:\n"
        "• supported — directly backed by the provided context\n"
        "• general — generic legal/procedural knowledge, no specific claim (amounts, "
        "deadlines, article contents) that needs a source\n"
        "• unsupported — a SPECIFIC claim (amount, deadline, condition, article content, "
        "court outcome) that the context does NOT back\n\n"
        "Return ONLY valid JSON:\n"
        '{"supported_count": N, "general_count": N, '
        '"unsupported": [{"statement": "...", "reason": "..."}]}\n\n'
        "Be strict about numbers, deadlines and article contents; do not flag stylistic "
        "or advisory sentences."
    ),
    description="Batched sentence-level faithfulness check (plan 2.3).",
    temperature=0.2,
    max_output_tokens=4096,
    response_format="json",
)


CITATION_VERIFIER = PromptTemplate(
    name="citation_verifier",
    role=PromptRole.SYSTEM,
    template=(
        "You are a Georgian law citation accuracy checker for კანონის ოსტატი.\n\n"

        "An AI generated a legal response that references specific Georgian law articles. "
        "Some of these citations could NOT be verified against our law database. "
        "Your job is to produce a CORRECTED version of the response where ALL "
        "law citations are accurate.\n\n"

        "═══ CORRECTION RULES ═══\n\n"

        "1. VERIFIED citations: Keep exactly as-is. Do not modify.\n\n"

        "2. FOUND_NOT_IN_CONTEXT citations: The AI cited an article WITHOUT having its "
        "text in context (the claim came from its memory). The ACTUAL article text from "
        "our database is provided. Compare every claim the response makes about this "
        "article against the ACTUAL text: keep claims the text confirms, and fix or "
        "remove anything the text does not support (amounts, deadlines, conditions).\n\n"

        "3. NOT_FOUND citations: The referenced article does NOT exist in our database. "
        "You MUST either:\n"
        "   a) Remove the citation and rephrase the surrounding text to remain coherent, OR\n"
        "   b) Replace it with a VERIFIED alternative that makes the same legal point "
        "(if one is available in the corrections above)\n"
        "   NEVER leave a NOT_FOUND citation in the response.\n\n"

        "═══ IMPORTANT ═══\n"
        "• Preserve the overall structure, tone, and language of the original response\n"
        "• Keep all non-citation content unchanged\n"
        "• If removing a citation makes a legal argument weaker, note this briefly\n"
        "• Respond in the SAME LANGUAGE as the original (Georgian or English)\n"
        "• Do NOT add citations that weren't in the original — only fix existing ones\n"
        "• Do NOT wrap your response in JSON or markdown — return the corrected text directly\n\n"

        "Return the FULL corrected response text."
    ),
    description="System instruction for Phase 3 — citation verification and correction via native chat.",
    temperature=1,
    max_output_tokens=16384,
    response_format="text",
)
