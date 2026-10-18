"""
Guardrail prompt — lightweight topic classification.
"""

from app.prompts import PromptRole, PromptTemplate


GUARDRAIL_CLASSIFIER = PromptTemplate(
    name="guardrail_classifier",
    role=PromptRole.USER,
    template=(
        "You are a legal topic classifier for a Georgian law application.\n"
        "Classify the user's message into exactly one category:\n"
        '- "legal": related to Georgian law, legal rights, court procedures, '
        "legal situations, employment disputes, property, family law, criminal, civil\n"
        '- "greeting": hello, how are you, introductions, etc.\n'
        '- "off_topic": weather, sports, recipes, coding, math, anything non-legal\n'
        '- "harmful": requests for illegal activity, threats, abuse, hacking instructions\n\n'
        'Respond with JSON: {{"category": "...", "confidence": 0.0-1.0}}\n\n'
        "IMPORTANT: Err on the side of \"legal\". If there's any chance the message "
        "relates to a legal situation (e.g., \"my boss fired me\", \"I was arrested\", "
        "\"my landlord won't return my deposit\"), classify as \"legal\".\n\n"
        "Georgian legal keywords to watch for: კანონი, სასამართლო, პოლიცია, "
        "ადვოკატი, ბრალი, სარჩელი, ხელშეკრულება, პატიმარი, ჯარიმა, "
        "უფლება, დანაშაული, არასრულწლოვანი, მკვლელობა, ქურდობა\n\n"
        'User\'s message: "{user_message}"'
    ),
    description="Classifies user messages as legal/greeting/off_topic/harmful before RAG runs.",
    variables=("user_message",),
    temperature=0.0,
    max_output_tokens=50,
    response_format="json",
)
