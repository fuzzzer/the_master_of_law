"""
Questionnaire prompts — AI question generation for pre-analysis intake.
"""

from app.prompts import PromptRole, PromptTemplate


QUESTIONNAIRE_GENERATOR = PromptTemplate(
    name="questionnaire_generator",
    role=PromptRole.USER,
    template=(
        "შენ ხარ გამოცდილი ქართველი იურისტი. მომხმარებელმა აღწერა იურიდიული სიტუაცია "
        "და შენ უნდა შეადგინო კითხვარი, რომელიც დაგეხმარება საქმის სრულად გაგებაში.\n\n"
        "იურიდიული სფერო: {legal_domain}\n\n"
        "მომხმარებლის აღწერა:\n{user_description}\n\n"
        "საბაზისო კითხვების შაბლონი (ამოსავალი წერტილი):\n{domain_template}\n\n"
        "წესები:\n"
        "1. შეადგინე 3-12 კითხვა, რომლებიც სპეციფიკურია ამ კონკრეტული საქმისთვის\n"
        "2. არ იკითხო ის, რაც მომხმარებელმა უკვე მოგვაწოდა აღწერაში\n"
        "3. ყველა კითხვა უნდა იყოს ქართულად\n"
        "4. ფოკუსირდი ფაქტებზე, რომლებიც მხოლოდ მომხმარებელმა იცის — არა ისეთზე, რაც კანონმდებლობიდან მოიძებნება\n"
        "5. თითოეულ კითხვას უნდა ჰქონდეს მკაფიო იურიდიული დანიშნულება\n"
        "6. question_id უნდა იყოს უნიკალური ინგლისური იდენტიფიკატორი (მაგ: incident_date, witnesses_present)\n\n"
        'დააბრუნე JSON მასივი:\n'
        '[{{\n'
        '  "question_id": "unique_id",\n'
        '  "question_text": "კითხვის ტექსტი ქართულად",\n'
        '  "question_type": "text|boolean|choice|date|number",\n'
        '  "options": ["ვარიანტი 1", "ვარიანტი 2"] (მხოლოდ choice ტიპისთვის, სხვა შემთხვევაში null),\n'
        '  "required": true/false,\n'
        '  "purpose": "რატომ არის ეს კითხვა მნიშვნელოვანი (ქართულად)",\n'
        '  "legal_relevance": "რომელ იურიდიულ არგუმენტს ემსახურება (ქართულად)"\n'
        '}}]\n\n'
        "დააბრუნე მხოლოდ JSON მასივი."
    ),
    description="Generates case-specific questionnaire questions based on legal domain and user description.",
    variables=("legal_domain", "user_description", "domain_template"),
    temperature=0.3,
    response_format="json",
)


NARRATIVE_EXTRACTOR = PromptTemplate(
    name="narrative_extractor",
    role=PromptRole.USER,
    template=(
        "შენ ხარ გამოცდილი ქართველი იურისტი. მომხმარებელმა თავისუფალი ტექსტით აღწერა "
        "იურიდიული სიტუაცია. შენ უნდა ამოიღო სტრუქტურირებული ინფორმაცია ამ ტექსტიდან.\n\n"
        "იურიდიული სფერო: {legal_domain}\n\n"
        "მომხმარებლის ნარატივი:\n{narrative}\n\n"
        "კითხვების შაბლონი (რა ინფორმაცია გვჭირდება):\n{domain_template}\n\n"
        "წესები:\n"
        "1. ამოიღე მხოლოდ ის ინფორმაცია, რაც ტექსტში ნამდვილად არის — არ გამოიგონო\n"
        "2. თუ ტექსტში ვერ იპოვე პასუხი, დატოვე answer_value null-ად\n"
        "3. boolean პასუხები გადააკეთე 'დიახ' ან 'არა' ფორმატში\n"
        "4. თარიღები გადააკეთე ISO ფორმატში (YYYY-MM-DD)\n"
        "5. რიცხვები დატოვე ციფრებით\n\n"
        'დააბრუნე JSON მასივი:\n'
        '[{{\n'
        '  "question_id": "template_question_id",\n'
        '  "question_text": "კითხვის ტექსტი",\n'
        '  "answer_value": "ამოღებული პასუხი ან null",\n'
        '  "answer_type": "text|boolean|choice|date|number"\n'
        '}}]\n\n'
        "დააბრუნე მხოლოდ JSON მასივი."
    ),
    description="Extracts structured answers from a free-text user narrative.",
    variables=("legal_domain", "narrative", "domain_template"),
    temperature=0.2,
    response_format="json",
)
