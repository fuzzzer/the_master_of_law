"""
Prompt template for AI-generated questionnaire questions.

Uses Gemini to create domain-specific, fact-finding questions in Georgian.
"""

from app.prompts import PromptRole, PromptTemplate

QUESTIONNAIRE_GENERATOR = PromptTemplate(
    name="questionnaire_generator",
    role=PromptRole.USER,
    description="Generates dynamic, domain-specific intake questions in Georgian",
    template="""
შენ ხარ ქართული სამართლის AI ასისტენტი. მომხმარებელმა აღწერა საკუთარი სიტუაცია და სისტემამ დაადგინა სამართლებრივი დარგი.

დაგენერირე **{max_questions}** შეკითხვა, რომელიც დაეხმარება მომხმარებელს მთლიანი სიტუაციის აღწერაში.

---

**სამართლებრივი დარგი:** {domain_name_ka} ({domain_key})

**მომხმარებლის აღწერა:**
{user_description}

**საუბრის ისტორია:**
{conversation_history}

**ბაზისური შაბლონის შეკითხვები (საწყისი წერტილი):**
{template_questions}

---

**ინსტრუქციები:**

1. ყველა შეკითხვა უნდა იყოს **ქართულ ენაზე**.
2. შეკითხვები უნდა იყოს **დარგ-სპეციფიკური** — არა ზოგადი, არამედ კონკრეტული სიტუაციისთვის.
3. თუ მომხმარებლის აღწერაში უკვე ნათქვამია რაიმე, ამის შესახებ შეკითხვა **არ დასვა**.
4. ყოველი შეკითხვა უნდა ეხებოდეს **ისეთ ფაქტებს, რომლებიც მომხმარებელს ეხმარება**, არა ისეთს, რაც კანონმდებლობიდან შეიძლება გაიგოს.
5. შეკითხვები უნდა იყოს დალაგებული **ლოგიკური თანმიმდევრობით**: რა მოხდა → როდის → სად → ვინ → რა დოკუმენტებია → რა შედეგი სურს.
6. სავალდებულო შეკითხვების რაოდენობა: **მინიმუმ 3, მაქსიმუმ {required_count}**.
7. თითოეულ შეკითხვას უნდა ჰქონდეს `purpose` და `legal_relevance` ქართულად.

---

**შეკითხვის ტიპები:**
- `text` — თავისუფალი ტექსტი (მრავალხაზიანი)
- `boolean` — კი/არა
- `choice` — ერთი ვარიანტის არჩევა (options ველით)
- `date` — თარიღი
- `number` — რიცხვი (თანხა, ვადა და ა.შ.)

---

**გამოტანის ფორმატი (JSON):**
[
  {{
    "question_id": "უნიკალური_id",
    "question_text_ka": "შეკითხვა ქართულად",
    "question_type": "text|boolean|choice|date|number",
    "options": ["ვარიანტი1", "ვარიანტი2"],
    "required": true|false,
    "purpose": "რატომ ვეკითხებით",
    "legal_relevance": "სამართლებრივი მნიშვნელობა"
  }}
]
""",
    variables=("domain_key", "domain_name_ka", "user_description", "conversation_history", "template_questions", "max_questions", "required_count"),
    temperature=0.3,
    response_format="json",
)

FOLLOW_UP_GENERATOR = PromptTemplate(
    name="questionnaire_follow_up",
    role=PromptRole.USER,
    description="Generates 1-2 follow-up questions based on a new answer",
    template="""
მომხმარებელმა უპასუხა შეკითხვას სამართლებრივ კითხვარში.

**სამართლებრივი დარგი:** {domain_name_ka}

**წინა შეკითხვა:** {previous_question}

**მიღებული პასუხი:** {user_answer}

**კონტექსტი:**
{context_summary}

თუ პასუხი გვიჩვენებს ახალ, მნიშვნელოვან ინფორმაციას, დაგენერირე 1-2 დამატებითი შეკითხვა.
თუ არა — დააბრუნე ცარიელი მასივი [].

გამოტანის ფორმატი (JSON):
[
  {{
    "question_id": "...",
    "question_text_ka": "...",
    "question_type": "...",
    "options": [],
    "required": true|false,
    "purpose": "...",
    "legal_relevance": "..."
  }}
]
""",
    variables=("domain_name_ka", "previous_question", "user_answer", "context_summary"),
    temperature=0.3,
    response_format="json",
)
