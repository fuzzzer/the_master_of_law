"""
Law connector schemas — what outside AI agents receive from the connector.

Every item that carries law or court text also carries where it came from
(``source_url``), how current it is (``version_date`` / ``in_force_since``,
with a ``version_note`` when the store does not record it) and the
not-legal-advice ``notice``. The connector returns sources only; the caller's
own AI writes the answer.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

NOT_LEGAL_ADVICE = (
    "ეს არის კანონის ტექსტი და წყარო, არა იურიდიული კონსულტაცია. ოფიციალური ტექსტი: "
    "matsne.gov.ge. This is law text and its source, not legal advice. The official "
    "text is on matsne.gov.ge; for important decisions consult a lawyer."
)

VERSION_UNKNOWN_NOTE = (
    "The date of this stored version is not recorded. Open source_url for the current "
    "consolidated text on matsne.gov.ge before relying on it."
)


class SourcedItem(BaseModel):
    """Fields every law-text result carries."""

    source_url: str = Field(description="Official matsne.gov.ge link for this text.")
    version_date: str | None = Field(
        default=None, description="Date of the consolidated version this text comes from."
    )
    in_force_since: str | None = Field(
        default=None, description="Date this article's current wording took effect, if known."
    )
    version_note: str | None = Field(
        default=None,
        description="Present when a version date is unknown or text may be incomplete.",
    )
    notice: str = Field(default=NOT_LEGAL_ADVICE)


class CodeSummary(SourcedItem):
    code: str = Field(description="Code identifier to pass to other tools, e.g. civil_code.")
    name: str = Field(description="Official Georgian name of the code.")
    article_count: int


class CodeList(BaseModel):
    codes: list[CodeSummary]
    notice: str = NOT_LEGAL_ADVICE


class ArticleHit(SourcedItem):
    id: str = Field(description="Stable id, usable with fetch: article:<code>:<number>.")
    code: str
    code_name: str
    article_number: str = Field(description="As printed in the law, e.g. 'მუხლი 369'.")
    article_title: str | None = None
    paragraph: str | None = Field(default=None, description="Paragraph the snippet is from.")
    snippet: str = Field(
        description="Exact text copied from the stored article (may be an excerpt)."
    )
    is_repealed: bool = False


class SearchLawResult(BaseModel):
    query: str
    found: bool
    results: list[ArticleHit]
    message: str | None = None
    notice: str = NOT_LEGAL_ADVICE


class Paragraph(BaseModel):
    number: str | None = None
    text: str


class ArticleRef(BaseModel):
    article_number: str
    article_title: str | None = None


class ArticleText(SourcedItem):
    id: str
    code: str
    code_name: str
    article_number: str
    article_title: str | None = None
    chapter: str | None = None
    text: str = Field(description="Full stored text of the article, unaltered.")
    paragraphs: list[Paragraph]
    requested_paragraph: Paragraph | None = None
    previous_article: ArticleRef | None = None
    next_article: ArticleRef | None = None
    is_repealed: bool = False


class GetArticleResult(BaseModel):
    found: bool
    article: ArticleText | None = None
    message: str | None = None
    notice: str = NOT_LEGAL_ADVICE


class ChapterSummary(BaseModel):
    chapter: str
    article_count: int
    first_article: str
    last_article: str


class CodeStructure(SourcedItem):
    found: bool
    code: str
    code_name: str | None = None
    chapters: list[ChapterSummary] = Field(default_factory=list)
    articles: list[ArticleRef] = Field(default_factory=list)
    total_articles: int = 0
    offset: int = 0
    message: str | None = None


class CourtDecision(BaseModel):
    id: str = Field(description="Stable id, usable with fetch: case:<collection>:<case id>.")
    case_number: str
    court: str
    collection: Literal["court_practice", "grand_chamber"]
    date: str | None = None
    year: str | None = None
    category: str | None = None
    snippet: str = Field(description="Exact text copied from the stored decision.")
    source_url: str | None = Field(
        default=None, description="Link to the decision or the publication it was taken from."
    )
    link_note: str | None = None
    notice: str = NOT_LEGAL_ADVICE


class CourtPracticeResult(BaseModel):
    query: str
    status: Literal["found", "none_found", "source_unavailable"]
    results: list[CourtDecision]
    message: str
    notice: str = NOT_LEGAL_ADVICE


class LexicalCheck(BaseModel):
    """Word and number overlap between the claim and the article text."""

    label: str = (
        "Word and number overlap only. This is not a legal judgement; read the text."
    )
    numbers_in_claim: list[str]
    numbers_found_in_text: list[str]
    numbers_not_in_text: list[str]
    claim_terms_found: int
    claim_terms_total: int


class VerifyCitationResult(BaseModel):
    exists: bool
    code: str
    article: str
    claim: str
    paragraph_requested: str | None = None
    paragraph_exists: bool | None = None
    is_repealed: bool = False
    article_number: str | None = None
    article_title: str | None = None
    text: str | None = Field(
        default=None, description="What the article (or requested paragraph) actually says."
    )
    source_url: str | None = None
    version_date: str | None = None
    in_force_since: str | None = None
    version_note: str | None = None
    lexical_check: LexicalCheck | None = None
    message: str
    notice: str = NOT_LEGAL_ADVICE


class SearchResultItem(BaseModel):
    """ChatGPT search tool item: id, title, url."""

    id: str
    title: str
    url: str


class SearchResults(BaseModel):
    results: list[SearchResultItem]


class FetchResult(BaseModel):
    """ChatGPT fetch tool document."""

    id: str
    title: str
    text: str
    url: str
    metadata: dict[str, str] | None = None


class VerifyCitationRequest(BaseModel):
    code: str = Field(description="Code id or Georgian name, e.g. civil_procedure_code.")
    article: str = Field(description="Article number, e.g. 369 or 166¹.")
    claim: str = Field(description="What the answer claims the article says.")
    paragraph: str | None = Field(
        default=None, description="Paragraph number, if the claim cites one."
    )
