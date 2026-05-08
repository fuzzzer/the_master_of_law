"""
Baseline questionnaire templates for the top 3 legal domains.

These serve as starting points for the AI question generator.
Each template contains domain-specific questions that are always
relevant, plus hints for the AI on what additional questions to ask.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TemplateQuestion:
    """A single baseline question in a domain template."""

    question_id: str
    question_text_ka: str
    question_type: str  # text, boolean, choice, date, number
    options: tuple[str, ...] = ()
    required: bool = True
    purpose: str = ""
    legal_relevance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_text_ka": self.question_text_ka,
            "question_type": self.question_type,
            "options": list(self.options),
            "required": self.required,
            "purpose": self.purpose,
            "legal_relevance": self.legal_relevance,
        }


@dataclass(frozen=True)
class DomainTemplate:
    """Baseline template for a legal domain."""

    domain_key: str
    domain_name_ka: str
    description: str
    questions: tuple[TemplateQuestion, ...]
    ai_hints: str = ""  # Extra guidance for the AI generator


# ── Criminal Law (სისხლის სამართალი) ──────────────────────────

CRIMINAL_TEMPLATE = DomainTemplate(
    domain_key="criminal",
    domain_name_ka="სისხლის სამართალი",
    description="Questions for criminal law cases — offenses, investigations, court proceedings",
    questions=(
        TemplateQuestion(
            question_id="crime_type",
            question_text_ka="რა სახის დანაშაული მოხდა? მოკლედ აღწერეთ.",
            question_type="text",
            required=True,
            purpose="დანაშაულის კვალიფიკაციის დადგენა",
            legal_relevance="სისხლის სამართლის კოდექსის შესაბამისი მუხლის შერჩევა",
        ),
        TemplateQuestion(
            question_id="date_of_incident",
            question_text_ka="როდის მოხდა დანაშაული? (ზუსტი თარიღი ან მიახლოებითი დრო)",
            question_type="date",
            required=True,
            purpose="საქმის ვადების გამოთვლა",
            legal_relevance="საპროცესო ვადების დადგენა და ვადაგასულობის შემოწმება",
        ),
        TemplateQuestion(
            question_id="police_involved",
            question_text_ka="მიმართეთ თუ არა პოლიციას ან პროკურატურას?",
            question_type="boolean",
            required=True,
            purpose="საგამოძიებო ეტაპის დადგენა",
            legal_relevance="საგამოძიებო მოქმედებების კანონიერების შემოწმება",
        ),
        TemplateQuestion(
            question_id="arrested",
            question_text_ka="გაწევრიანებული ხართ თუ არა საქმეში როგორც ბრალდებული ან მსხვერპლი?",
            question_type="choice",
            options=("ბრალდებული", "მსხვერპლი", "მოწმე", "სხვა"),
            required=True,
            purpose="მხარის სტატუსის დადგენა",
            legal_relevance="უფლებებისა და ვალდებულებების განსაზღვრა",
        ),
        TemplateQuestion(
            question_id="evidence",
            question_text_ka="არსებობს თუ არა მტკიცებულებები (ვიდეო, ფოტო, მოწმეები)?",
            question_type="text",
            required=False,
            purpose="მტკიცებულებების შეფასება",
            legal_relevance="მტკიცებულებათა სისტემის ანალიზი",
        ),
    ),
    ai_hints="""
შეკითხვები უნდა იყოს დანაშაულის სპეციფიკური. გაითვალისწინეთ:
- დანაშაულის თარიღი და ადგილი
- საგამოძიებო ორგანოების ჩართულობა
- დაკავების ფაქტი და ვადები
- ადვოკატის დანიშვნა
- შეწყალების ან პატიმრობის გათავისუფლების საკითხები
""",
)


# ── Labor Law (შრომის სამართალი) ──────────────────────────────

LABOR_TEMPLATE = DomainTemplate(
    domain_key="labor",
    domain_name_ka="შრომის სამართალი",
    description="Questions for labor law cases — dismissal, wages, contracts, discrimination",
    questions=(
        TemplateQuestion(
            question_id="employment_status",
            question_text_ka="რა სახის შრომითი ურთიერთობა გაქვთ? (შრომითი ხელშეკრულება, გრაფიკი, ვადიანი/უვადო)",
            question_type="text",
            required=True,
            purpose="შრომითი ურთიერთობის ფორმის დადგენა",
            legal_relevance="შრომის კოდექსის მოქმედების სფეროს განსაზღვრა",
        ),
        TemplateQuestion(
            question_id="employer_name",
            question_text_ka="რა ორგანიზაციაში მუშაობთ? (დამსაქმებლის სახელი)",
            question_type="text",
            required=True,
            purpose="დამსაქმებლის იდენტიფიკაცია",
            legal_relevance="მოქმედი კანონმდებლობის შერჩევა სექტორის მიხედვით",
        ),
        TemplateQuestion(
            question_id="problem_type",
            question_text_ka="რა პრობლემა გაქვთ? (დათხოვნა, ხელფასი, უსაფრთხოება, დისკრიმინაცია)",
            question_type="choice",
            options=("დათხოვნა", "ხელფასის არ გადახდა", "უსაფრთხოების დარღვევა", "დისკრიმინაცია", "სხვა"),
            required=True,
            purpose="საკითხის კატეგორიზაცია",
            legal_relevance="შრომის კოდექსის შესაბამისი მუხლების იდენტიფიკაცია",
        ),
        TemplateQuestion(
            question_id="employment_duration",
            question_text_ka="რამდენი ხანი მუშაობთ ამ სამსახურში? (თვე/წელი)",
            question_type="text",
            required=True,
            purpose="სტაჟის დადგენა",
            legal_relevance="კომპენსაციისა და უფლებების გამოთვლა",
        ),
        TemplateQuestion(
            question_id="written_contract",
            question_text_ka="გაქვთ თუ არა ხელშეკრულება წერილობით?",
            question_type="boolean",
            required=True,
            purpose="ხელშეკრულების ფორმის დადგენა",
            legal_relevance="მტკიცებულებების სისტემა და ვადების აღდგენა",
        ),
    ),
    ai_hints="""
შეკითხვები უნდა იყოს შრომითი ურთიერთობის სპეციფიკური. გაითვალისწინეთ:
- დამსაქმებლის ტიპი (კერძო/საჯარო/ეკონომიკური საქმიანობა)
- ხელშეკრულების ფორმა (წერილობითი/ზეპირი)
- სამუშაო საათები და ზეგანაკვეთა
- შეწყვეტის საფუძველი და ვადები
- კომპენსაციისა და სარჩელის ვადები
""",
)


# ── Civil Law (სამოქალაქო სამართალი) ──────────────────────────

CIVIL_TEMPLATE = DomainTemplate(
    domain_key="civil",
    domain_name_ka="სამოქალაქო სამართალი",
    description="Questions for civil law cases — contracts, damages, property, debts",
    questions=(
        TemplateQuestion(
            question_id="dispute_subject",
            question_text_ka="რა საკითხზე გსურთ კონსულტაცია? (ხელშეკრულება, ზიანი, ვალი, საკუთრება)",
            question_type="choice",
            options=("ხელშეკრულება", "ზიანის ანაზღაურება", "ვალის დაბრუნება", "საკუთრება", "სხვა"),
            required=True,
            purpose="საკითხის კატეგორიის დადგენა",
            legal_relevance="სამოქალაქო კოდექსის შესაბამისი ნაწილის შერჩევა",
        ),
        TemplateQuestion(
            question_id="parties",
            question_text_ka="ვინ არის საქმის მხარეები? (თქვენი როლი და მეორე მხარის ინფორმაცია)",
            question_type="text",
            required=True,
            purpose="მხარეების იდენტიფიკაცია",
            legal_relevance="მხარეთა უფლებებისა და ვალდებულებების განსაზღვრა",
        ),
        TemplateQuestion(
            question_id="contract_exists",
            question_text_ka="არსებობს თუ არა წერილობითი ხელშეკრულება ან დოკუმენტი?",
            question_type="boolean",
            required=True,
            purpose="მტკიცებულებების არსებობის დადგენა",
            legal_relevance="სამოქალაქო საპროცესო კოდექსის მტკიცებულებათა სისტემა",
        ),
        TemplateQuestion(
            question_id="desired_outcome",
            question_text_ka="რა შედეგის მიღწევა გსურთ? (კომპენსაცია, ვალის დაბრუნება, ხელშეკრულების შეწყვეტა)",
            question_type="text",
            required=True,
            purpose="მომხმარებლის მიზნის გაგება",
            legal_relevance="სარჩელის ტიპისა და სამართლებრივი საფუძლის შერჩევა",
        ),
        TemplateQuestion(
            question_id="amount_in_dispute",
            question_text_ka="თუ მოქმედებს ფულადი თანხა, რა ოდენობაა საქმეში? (ლარი)",
            question_type="number",
            required=False,
            purpose="საქმის ღირებულების დადგენა",
            legal_relevance="სასამართლო ბაჟის გამოთვლა და იურისდიქციის განსაზღვრა",
        ),
    ),
    ai_hints="""
შეკითხვები უნდა იყოს სამოქალაქო სამართლის სპეციფიკური. გაითვალისწინეთ:
- ხელშეკრულების ტიპი და პირობები
- დარღვევის თარიღი და ფაქტები
- მორალური ზიანი და ანაზღაურების მოთხოვნა
- ვალდებულებების შესრულება და დაგვიანება
- სარჩელის ვადები და ვადაგადაცილების შემთხვევები
""",
)


# Registry lookup
DOMAIN_TEMPLATES: dict[str, DomainTemplate] = {
    t.domain_key: t
    for t in (CRIMINAL_TEMPLATE, LABOR_TEMPLATE, CIVIL_TEMPLATE)
}


def get_domain_template(domain_key: str) -> DomainTemplate | None:
    """Get the baseline template for a legal domain."""
    return DOMAIN_TEMPLATES.get(domain_key)


def list_template_domains() -> list[str]:
    """List all domains with baseline templates."""
    return list(DOMAIN_TEMPLATES.keys())
