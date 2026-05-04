"""
Case builder prompts — defense case file generation.
"""

from app.prompts import PromptRole, PromptTemplate


CASE_BUILDER = PromptTemplate(
    name="case_builder",
    role=PromptRole.USER,
    template=(
        "You are კანონის ოსტატი (The Master of Law). Based on the conversation "
        "and retrieved law articles below, generate a comprehensive DEFENSE CASE FILE.\n\n"
        "CONVERSATION:\n{conversation_text}\n\n"
        "RETRIEVED LAW ARTICLES:\n{law_context}\n\n"
        "Generate the case file as a JSON object with these exact keys:\n"
        "{{\n"
        '  "title": "Auto-generated case title in Georgian",\n'
        '  "facts": {{\n'
        '    "what_happened": "...",\n'
        '    "when": "...",\n'
        '    "where": "...",\n'
        '    "who_involved": "...",\n'
        '    "key_evidence": "..."\n'
        "  }},\n"
        '  "evidence": {{\n'
        '    "has": ["list of evidence the user already has"],\n'
        '    "needs": ["list of evidence the user needs to collect"],\n'
        '    "recommended_types": ["recommended evidence types"],\n'
        '    "deadlines": ["evidence preservation deadlines"]\n'
        "  }},\n"
        '  "applicable_laws": {{\n'
        '    "favorable": [{{"code": "...", "article": "...", "explanation": "...", "url": "..."}}],\n'
        '    "against": [{{"code": "...", "article": "...", "explanation": "...", "url": "..."}}],\n'
        '    "neutral": [{{"code": "...", "article": "...", "explanation": "...", "url": "..."}}]\n'
        "  }},\n"
        '  "defense_strategies": [\n'
        "    {{\n"
        '      "name": "...",\n'
        '      "success_likelihood": "...",\n'
        '      "risk_level": "...",\n'
        '      "legal_basis": ["articles"],\n'
        '      "how_it_works": "...",\n'
        '      "what_you_need": "...",\n'
        '      "risks": "..."\n'
        "    }}\n"
        "  ],\n"
        '  "prosecution_args": [\n'
        "    {{\n"
        '      "argument": "what they\'ll say",\n'
        '      "counter": "your response"\n'
        "    }}\n"
        "  ],\n"
        '  "action_checklist": [\n'
        "    {{\n"
        '      "deadline": "Immediate|Within 48h|Within 3 days|Within 1 month|Before court",\n'
        '      "action": "what to do",\n'
        '      "done": false\n'
        "    }}\n"
        "  ],\n"
        '  "lawyer_brief": {{\n'
        '    "key_points": ["what to tell your lawyer"],\n'
        '    "questions_to_ask": ["questions for lawyer"],\n'
        '    "documents_to_bring": ["list of documents"]\n'
        "  }},\n"
        '  "citations": [\n'
        "    {{\n"
        '      "code": "...",\n'
        '      "article": "...",\n'
        '      "text": "...",\n'
        '      "url": "..."\n'
        "    }}\n"
        "  ]\n"
        "}}\n\n"
        "IMPORTANT:\n"
        "- Write in Georgian (ქართული)\n"
        "- Every law reference must cite a specific article\n"
        "- Use ONLY laws from the provided context — never fabricate\n"
        "- Include both favorable AND unfavorable laws\n"
        "- Be thorough — this document may be used in court\n\n"
        "Return ONLY the JSON object, no markdown wrapping."
    ),
    description="Generates a structured 8-section defense case file from conversation + law context.",
    variables=("conversation_text", "law_context"),
    temperature=0.1,
    response_format="json",
)
