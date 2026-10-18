"""
Domain-specific baseline question templates for the questionnaire engine.

The AI uses these as a starting point, then adapts based on the specific case context.
"""

from __future__ import annotations


DOMAIN_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "criminal": [
        {"id": "incident_date", "text": "ზუსტად როდის მოხდა ინციდენტი?", "type": "date"},
        {"id": "charges", "text": "რა ბრალდება წაგიყენეს ან რა დანაშაულს გედავებიან?", "type": "text"},
        {"id": "arrest_details", "text": "მოხდა თუ არა დაკავება? თუ კი, როდის და სად?", "type": "text"},
        {"id": "witnesses_present", "text": "იყვნენ თუ არა მოწმეები?", "type": "boolean"},
        {"id": "witness_details", "text": "ვინ არიან მოწმეები და რა იციან?", "type": "text"},
        {"id": "evidence_available", "text": "რა მტკიცებულებები არსებობს? (ვიდეო, ფოტო, დოკუმენტები)", "type": "text"},
        {"id": "prior_record", "text": "გაქვთ თუ არა წინა ნასამართლობა?", "type": "boolean"},
        {"id": "lawyer_involved", "text": "გყავთ თუ არა ამჟამად ადვოკატი?", "type": "boolean"},
        {"id": "police_statement", "text": "მისცეთ თუ არა ჩვენება პოლიციას?", "type": "boolean"},
        {"id": "injury_damage", "text": "მოხდა თუ არა ფიზიკური დაზიანება ან მატერიალური ზარალი?", "type": "text"},
    ],
    "labor": [
        {"id": "employment_start", "text": "როდის დაიწყეთ მუშაობა?", "type": "date"},
        {"id": "employment_end", "text": "როდის დასრულდა/შეწყდა შრომითი ურთიერთობა?", "type": "date"},
        {"id": "contract_type", "text": "რა ტიპის შრომითი ხელშეკრულება გქონდათ?", "type": "choice"},
        {"id": "termination_reason", "text": "რა მიზეზით მოხდა სამსახურიდან გათავისუფლება?", "type": "text"},
        {"id": "written_notice", "text": "მიიღეთ თუ არა წერილობითი შეტყობინება?", "type": "boolean"},
        {"id": "salary_owed", "text": "გრჩებათ თუ არა მიუღებელი ხელფასი? რა ოდენობის?", "type": "text"},
        {"id": "documentation", "text": "რა დოკუმენტაცია გაქვთ? (ხელშეკრულება, ხელფასის ქვითარი, წერილები)", "type": "text"},
        {"id": "employer_size", "text": "რამდენი თანამშრომელი ჰყავს დამსაქმებელს?", "type": "number"},
    ],
    "civil": [
        {"id": "parties_involved", "text": "ვინ არიან მხარეები? (ფიზიკური/იურიდიული პირები)", "type": "text"},
        {"id": "contract_exists", "text": "არსებობს თუ არა წერილობითი ხელშეკრულება?", "type": "boolean"},
        {"id": "contract_date", "text": "როდის დაიდო ხელშეკრულება/შეთანხმება?", "type": "date"},
        {"id": "dispute_amount", "text": "რა არის დავის ოდენობა ლარებში?", "type": "number"},
        {"id": "timeline", "text": "აღწერეთ მოვლენების ქრონოლოგია", "type": "text"},
        {"id": "damages_type", "text": "რა ტიპის ზიანი მოგადგათ? (მატერიალური, მორალური)", "type": "text"},
        {"id": "prior_communication", "text": "იყო თუ არა მოლაპარაკების მცდელობა მეორე მხარესთან?", "type": "boolean"},
        {"id": "evidence_docs", "text": "რა დოკუმენტები/მტკიცებულებები გაქვთ?", "type": "text"},
    ],
    "family": [
        {"id": "relationship_type", "text": "რა ტიპის ოჯახური ურთიერთობაა? (ქორწინება, თანაცხოვრება)", "type": "text"},
        {"id": "marriage_date", "text": "როდის დაქორწინდით?", "type": "date"},
        {"id": "children", "text": "გყავთ თუ არა საერთო შვილები?", "type": "boolean"},
        {"id": "children_ages", "text": "რა ასაკისაა შვილი/შვილები?", "type": "text"},
        {"id": "property_shared", "text": "არსებობს თუ არა საერთო ქონება?", "type": "boolean"},
        {"id": "violence", "text": "იყო თუ არა ძალადობის ფაქტი?", "type": "boolean"},
    ],
    "administrative": [
        {"id": "authority_name", "text": "რომელი ადმინისტრაციული ორგანოა ჩართული?", "type": "text"},
        {"id": "decision_date", "text": "როდის მიიღეს გადაწყვეტილება?", "type": "date"},
        {"id": "fine_amount", "text": "რა ოდენობის ჯარიმა/სანქცია დაგეკისრათ?", "type": "number"},
        {"id": "appealed", "text": "გაასაჩივრეთ თუ არა გადაწყვეტილება?", "type": "boolean"},
        {"id": "deadline", "text": "აქვს თუ არა გასაჩივრებას ვადა? როდის იწურება?", "type": "date"},
    ],
}

# Fallback template for domains not listed above
_GENERIC_TEMPLATE: list[dict[str, str]] = [
    {"id": "event_description", "text": "დეტალურად აღწერეთ მოვლენა", "type": "text"},
    {"id": "event_date", "text": "როდის მოხდა?", "type": "date"},
    {"id": "parties", "text": "ვინ არიან ჩართული მხარეები?", "type": "text"},
    {"id": "documents", "text": "რა დოკუმენტაცია გაქვთ?", "type": "text"},
    {"id": "desired_outcome", "text": "რა შედეგს ელოდებით?", "type": "text"},
]


def get_domain_template(domain: str) -> str:
    """Format a domain's template as a string for the Gemini prompt."""
    questions = DOMAIN_TEMPLATES.get(domain, _GENERIC_TEMPLATE)
    lines = []
    for q in questions:
        lines.append(f"- [{q['type']}] {q['text']} (id: {q['id']})")
    return "\n".join(lines)
