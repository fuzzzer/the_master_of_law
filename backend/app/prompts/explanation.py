"""
Explanation prompts — legal language simplification.
"""

from app.prompts import PromptRole, PromptTemplate


SIMPLIFY_TEXT = PromptTemplate(
    name="explain_simplify",
    role=PromptRole.USER,
    template=(
        "You are a Georgian legal language simplifier. Your job is to take complex "
        "legal text and rewrite it so that a regular person with no legal education "
        "can understand it completely.\n\n"
        "RULES:\n"
        "1. Use everyday Georgian language — no legal jargon\n"
        "2. If a legal term must be used, immediately explain what it means in parentheses\n"
        "3. Use concrete examples to illustrate abstract concepts\n"
        "4. Keep sentences short and clear\n"
        "5. Preserve the MEANING accurately — don't oversimplify to the point of incorrectness\n"
        "6. Format with bullet points for clarity\n"
        "7. If the text references specific articles or codes, keep those references "
        "but explain what they mean\n\n"
        "LEGAL TEXT TO SIMPLIFY:\n{legal_text}\n\n"
        "Write your simplified explanation in Georgian (ქართული). "
        "If the input is in English, respond in English."
    ),
    description="Simplifies complex legal text into plain language for laypersons.",
    variables=("legal_text",),
    temperature=0.2,
    max_output_tokens=4096,
)


EXPLAIN_ARTICLE = PromptTemplate(
    name="explain_article",
    role=PromptRole.USER,
    template=(
        "Explain this Georgian law article in simple, everyday language.\n\n"
        "LAW: {code_name}, {article_number}\n"
        "ARTICLE TEXT:\n{article_text}\n\n"
        "Explain:\n"
        "1. What this article means in plain language\n"
        "2. When it applies (give a real-world example)\n"
        "3. What consequences it describes\n"
        "4. Important details people often miss\n\n"
        "Write in Georgian (ქართული). If input is English, respond in English."
    ),
    description="Explains a specific law article with practical examples and consequences.",
    variables=("code_name", "article_number", "article_text"),
    temperature=0.2,
    max_output_tokens=4096,
)
