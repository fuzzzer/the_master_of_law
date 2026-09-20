"""
Document generation prompts — drafts legal documents and identifies dispatch info.
"""

from app.prompts import PromptRole, PromptTemplate

DOCUMENT_DRAFTER = PromptTemplate(
    name="document_drafter",
    role=PromptRole.USER,
    template=(
        "You are ბუნდოვანი კანონი (Fuzzzy Law), an expert Georgian lawyer.\n"
        "Your task is to draft a fully formatted, official legal document (e.g. {document_type}) "
        "ready for submission, based on the provided Case File information.\n\n"
        "Also, review the provided 'Beneficial Contacts' and determine where exactly "
        "this document should be sent (e.g. which official body).\n\n"
        "CASE FILE SUMMARY:\n"
        "{case_data}\n\n"
        "BENEFICIAL CONTACTS (for determining dispatch info):\n"
        "{contacts_data}\n\n"
        "OUTPUT FORMAT (Return a JSON object with these exact keys):\n"
        "{{\n"
        '  "dispatch_info": {{\n'
        '    "target_body": "Name of the government body or court to send this to",\n'
        '    "email": "Email if available, otherwise empty",\n'
        '    "address": "Address if available, otherwise empty",\n'
        '    "instructions": "Brief instructions on how to send it (e.g. print 2 copies, sign, send via post or email)"\n'
        "  }},\n"
        '  "document_markdown": "The FULL TEXT of the legal document, formatted with Markdown headers, bold text, and placeholders like [სახელი გვარი] where user info is missing. Make it sound highly professional, formal, and legally precise."\n'
        "}}\n\n"
        "IMPORTANT RULES:\n"
        "- The document must be in Georgian (ქართული).\n"
        "- It must include standard legal document structure (Addressee, Applicant, Subject, Body, Legal Basis, Request, Signature).\n"
        "- Use markdown for formatting (`#` for titles, `**` for bold).\n"
        "- Return ONLY the JSON object, no wrapping markdown blocks."
    ),
    description="Drafts a formal Georgian legal document and determines where to send it.",
    variables=("document_type", "case_data", "contacts_data"),
    temperature=0.7,
    response_format="json",
)
