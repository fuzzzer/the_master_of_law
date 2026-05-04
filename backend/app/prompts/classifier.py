"""
Legal classifier prompts — domain classification.
"""

from app.prompts import PromptRole, PromptTemplate


LEGAL_CLASSIFIER = PromptTemplate(
    name="legal_classifier",
    role=PromptRole.USER,
    template=(
        "You are a Georgian legal expert. Classify the user's legal situation "
        "into one or more legal domains.\n\n"
        "USER'S SITUATION:\n{user_message}\n\n"
        "Available domains:\n"
        "- criminal: სისხლის სამართალი (criminal offenses, charges, defense)\n"
        "- civil: სამოქალაქო სამართალი (contracts, property, damages, obligations)\n"
        "- administrative: ადმინისტრაციული სამართალი (government actions, permits, fines)\n"
        "- labor: შრომის სამართალი (employment, dismissal, workplace rights)\n"
        "- family: საოჯახო სამართალი (marriage, divorce, custody, inheritance)\n"
        "- tax: საგადასახადო სამართალი (tax disputes, penalties)\n"
        "- land: მიწის სამართალი (property, land ownership, boundaries)\n"
        "- constitutional: კონსტიტუციური სამართალი (fundamental rights, constitutional violations)\n"
        "- commercial: სამეწარმეო სამართალი (business, corporate, entrepreneurial)\n\n"
        "Return a JSON object:\n"
        '{{"primary": "domain_key", "secondary": ["other_relevant_domains"], '
        '"confidence": 0.0-1.0, "reasoning": "brief explanation"}}\n\n'
        "Return ONLY the JSON object."
    ),
    description="Classifies a user's legal situation into one of 9 Georgian legal domains.",
    variables=("user_message",),
    temperature=0.1,
    response_format="json",
)
