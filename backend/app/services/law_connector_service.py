"""
Law Connector Service — Georgian law sources for outside AI agents.

Backs the MCP server and its REST mirror. It never calls a model: it returns
exact stored text with its official link and version date, and the caller's
own AI (ChatGPT, Claude, any agent) writes the answer from it. Statutes come
from the article store (the same deterministic store the app's own pipeline
grounds on); court decisions come from the court-practice collections by
plain text match, so the lookup works without anyone's model key.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.integrations.chroma_client import ChromaClient, get_chroma_client
from app.schemas.connector_schema import (
    VERSION_UNKNOWN_NOTE,
    ArticleHit,
    ArticleRef,
    ArticleText,
    ChapterSummary,
    CodeList,
    CodeStructure,
    CodeSummary,
    CourtDecision,
    CourtPracticeResult,
    FetchResult,
    GetArticleResult,
    LexicalCheck,
    Paragraph,
    SearchLawResult,
    SearchResultItem,
    SearchResults,
    VerifyCitationResult,
)
from app.services.article_store_service import (
    ArticleStoreService,
    _normalize_article,
    get_article_store_service,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

MATSNE_DOCUMENT_URL = "https://matsne.gov.ge/ka/document/view/{document_number}"

# matsne.gov.ge document numbers of the codes in the store, used to build the
# official link when a store row carries none.
MATSNE_DOCUMENT_NUMBERS = {
    "admin_offences_code": "28216",
    "admin_procedure_code": "16492",
    "civil_code": "31702",
    "civil_procedure_code": "29962",
    "constitution": "30346",
    "criminal_code": "16426",
    "criminal_procedure_code": "90034",
    "election_code": "1557168",
    "general_admin_code": "16270",
    "labour_code": "1155567",
    "personal_data_law": "1561437",
    "tax_code": "1043717",
}

CODE_VERSION_COLUMNS = ("version_date", "consolidated_version_date", "consolidated_date")
ARTICLE_IN_FORCE_COLUMNS = ("in_force_since", "effective_date")

COURT_COLLECTIONS = ("court_practice", "grand_chamber")
COURT_NAMES = {
    "court_practice": "საქართველოს უზენაესი სასამართლო (Supreme Court of Georgia)",
    "grand_chamber": (
        "საქართველოს უზენაესი სასამართლოს დიდი პალატა (Supreme Court of Georgia, Grand Chamber)"
    ),
}
COURT_LINK_NOTE = (
    "No direct link is stored for this decision. Look the case number up on "
    "supremecourt.ge before citing it."
)
COURT_SITE_URL = "https://www.supremecourt.ge"

SNIPPET_CHARS = 600
MAX_SEARCH_LIMIT = 25
MAX_BROWSE_LIMIT = 300

_WORD = re.compile(r"[\wა-ჿ]+")
_NUMBER = re.compile(r"\d+")


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _stem(word: str) -> str:
    """Crude Georgian stem: drop the case ending so inflected forms match."""
    if len(word) >= 6:
        return word[:-2]
    if len(word) >= 4:
        return word[:-1]
    return word


def _excerpt(text: str, limit: int = SNIPPET_CHARS) -> str:
    """Leading part of ``text``, cut at a word boundary; the words are unaltered."""
    if len(text) <= limit:
        return text
    cut = text.rfind(" ", 0, limit)
    return text[: cut if cut > 0 else limit] + " …"


def _first_present(row: dict[str, Any], columns: tuple[str, ...]) -> str | None:
    for column in columns:
        value = row.get(column)
        if value:
            return str(value)
    return None


class LawConnectorService:
    """Read-only law and court-practice lookups that always name their source."""

    def __init__(
        self,
        store: ArticleStoreService | None = None,
        chroma: ChromaClient | None = None,
    ) -> None:
        self._store = store or get_article_store_service()
        self._chroma = chroma
        self._codes: dict[str, dict[str, Any]] | None = None
        self._article_order: dict[str, list[ArticleRef]] = {}

    # ── Sources and versions ─────────────────────────────────

    def _code_rows(self) -> dict[str, dict[str, Any]]:
        if self._codes is None:
            self._codes = {c["document_id"]: c for c in self._store.list_codes()}
        return self._codes

    def _code_url(self, document_id: str) -> str:
        code = self._code_rows().get(document_id, {})
        url = code.get("matsne_url") or code.get("source_url")
        if url:
            return str(url)
        number = code.get("document_number") or MATSNE_DOCUMENT_NUMBERS.get(document_id)
        if number:
            return MATSNE_DOCUMENT_URL.format(document_number=number)
        return "https://matsne.gov.ge"

    def _article_url(self, art: dict[str, Any]) -> str:
        url = art.get("matsne_url") or art.get("article_url")
        if url:
            return str(url)
        anchor = _normalize_article(art["article_number"])
        return f"{self._code_url(art['document_id'])}#article_{anchor}"

    def _version(self, art: dict[str, Any]) -> dict[str, str | None]:
        """version_date / in_force_since / version_note for an article."""
        code = self._code_rows().get(art["document_id"], {})
        version_date = art.get("version_date") or _first_present(code, CODE_VERSION_COLUMNS)
        in_force_since = _first_present(art, ARTICLE_IN_FORCE_COLUMNS)
        notes: list[str] = []
        if not version_date and not in_force_since:
            notes.append(VERSION_UNKNOWN_NOTE)
        gap = self._paragraph_gap(art)
        if gap:
            notes.append(gap)
        return {
            "version_date": str(version_date) if version_date else None,
            "in_force_since": in_force_since,
            "version_note": " ".join(notes) or None,
        }

    @staticmethod
    def _paragraph_gap(art: dict[str, Any]) -> str | None:
        """Flag a stored text whose numbered paragraphs do not start at 1."""
        numbers = [str(p.get("number")) for p in art.get("paragraphs") or [] if p.get("number")]
        if numbers and numbers[0].isdigit() and numbers[0] != "1":
            return (
                f"The stored text starts at paragraph {numbers[0]}; earlier paragraphs may "
                "be missing. Check source_url for the full article."
            )
        return None

    @staticmethod
    def _article_id(art: dict[str, Any]) -> str:
        return f"article:{art['document_id']}:{_normalize_article(art['article_number'])}"

    # ── Tools ────────────────────────────────────────────────

    def list_codes(self) -> CodeList:
        """Every code in the store with its article count, link and version date."""
        codes = []
        for document_id, row in sorted(self._code_rows().items()):
            version_date = _first_present(row, CODE_VERSION_COLUMNS)
            codes.append(CodeSummary(
                code=document_id,
                name=row["code_name"],
                article_count=row.get("article_count") or 0,
                source_url=self._code_url(document_id),
                version_date=version_date,
                version_note=None if version_date else VERSION_UNKNOWN_NOTE,
            ))
        return CodeList(codes=codes)

    def search_law(self, query: str, code: str | None = None, limit: int = 8) -> SearchLawResult:
        """Articles matching the query, best first, each with an exact snippet."""
        limit = max(1, min(limit, MAX_SEARCH_LIMIT))
        document_id = None
        if code:
            document_id = self._store.resolve_code(code)
            if document_id is None:
                return SearchLawResult(
                    query=query, found=False, results=[],
                    message=f"Unknown code '{code}'. Call list_codes for the available codes.",
                )
        rows = self._store.fts_search(query, limit=limit, document_id=document_id)
        if len(rows) < limit:
            seen = {r["article_id"] for r in rows}
            more = self._store.fts_search(
                query, limit=limit * 2, document_id=document_id, match_any=True
            )
            rows += [r for r in more if r["article_id"] not in seen][: limit - len(rows)]
        hits = [self._hit(r, query) for r in rows]
        return SearchLawResult(
            query=query,
            found=bool(hits),
            results=hits,
            message=None if hits else (
                "No article matched. Try other words (Georgian legal terms work best) or "
                "browse_code. Do not answer from memory."
            ),
        )

    def _hit(self, art: dict[str, Any], query: str) -> ArticleHit:
        number, text = self._best_paragraph(art, query)
        return ArticleHit(
            id=self._article_id(art),
            code=art["document_id"],
            code_name=art["code_name"],
            article_number=art["article_number"],
            article_title=art.get("article_title"),
            paragraph=number,
            snippet=_excerpt(text),
            is_repealed=art.get("is_repealed", False),
            source_url=self._article_url(art),
            **self._version(art),
        )

    @staticmethod
    def _best_paragraph(art: dict[str, Any], query: str) -> tuple[str | None, str]:
        """The paragraph sharing most word stems with the query."""
        stems = {_stem(w) for w in _words(query) if len(w) >= 3}
        best: tuple[int, str | None, str] = (-1, None, art["content_ka"])
        for p in art.get("paragraphs") or []:
            text = p.get("text") or ""
            lowered = text.lower()
            score = sum(1 for s in stems if s in lowered)
            if score > best[0]:
                best = (score, p.get("number"), text)
        return best[1], best[2]

    def get_article(
        self, code: str, article: str, paragraph: str | None = None
    ) -> GetArticleResult:
        """Full exact article text with link, version and neighbouring articles."""
        art = self._lookup(code, article, paragraph)
        if art is None:
            return GetArticleResult(found=False, message=self._not_found_message(code, article))
        document_id = art["document_id"]
        prev_ref, next_ref = self._neighbours(document_id, art["article_number"])
        requested = None
        if paragraph and art.get("paragraph"):
            found = art["paragraph"]
            requested = Paragraph(number=found.get("number"), text=found["text"])
        message = None
        if paragraph and requested is None:
            message = f"Paragraph {paragraph} is not in the stored text of this article."
        return GetArticleResult(
            found=True,
            message=message,
            article=ArticleText(
                id=self._article_id(art),
                code=document_id,
                code_name=art["code_name"],
                article_number=art["article_number"],
                article_title=art.get("article_title"),
                chapter=art.get("chapter"),
                text=art["content_ka"],
                paragraphs=[
                    Paragraph(number=p.get("number"), text=p.get("text") or "")
                    for p in art.get("paragraphs") or []
                ],
                requested_paragraph=requested,
                previous_article=prev_ref,
                next_article=next_ref,
                is_repealed=art.get("is_repealed", False),
                source_url=self._article_url(art),
                **self._version(art),
            ),
        )

    def _lookup(self, code: str, article: str, paragraph: str | None) -> dict[str, Any] | None:
        """Exact article, only within a known code (never a guess across codes)."""
        if self._store.resolve_code(code) is None:
            return None
        return self._store.get_article(code, article, paragraph)

    def _not_found_message(self, code: str, article: str) -> str:
        if self._store.resolve_code(code) is None:
            return f"Unknown code '{code}'. Call list_codes for the available codes."
        return (
            f"Article {article} is not in the stored text of '{code}'. It may not exist; do "
            "not cite it. Check the official text on matsne.gov.ge."
        )

    def _ordered_articles(self, document_id: str) -> list[ArticleRef]:
        if document_id not in self._article_order:
            self._article_order[document_id] = [
                ArticleRef(article_number=a["article_number"], article_title=a.get("article_title"))
                for a in self._store.get_code_articles(document_id)
            ]
        return self._article_order[document_id]

    def _neighbours(
        self, document_id: str, article_number: str
    ) -> tuple[ArticleRef | None, ArticleRef | None]:
        refs = self._ordered_articles(document_id)
        for i, ref in enumerate(refs):
            if ref.article_number == article_number:
                prev_ref = refs[i - 1] if i > 0 else None
                next_ref = refs[i + 1] if i + 1 < len(refs) else None
                return prev_ref, next_ref
        return None, None

    def browse_code(
        self, code: str, chapter: str | None = None, offset: int = 0, limit: int = 200
    ) -> CodeStructure:
        """Chapters of a code, or the article list (numbers and titles) of one chapter."""
        document_id = self._store.resolve_code(code)
        if document_id is None:
            return CodeStructure(
                found=False, code=code, source_url="https://matsne.gov.ge",
                message=f"Unknown code '{code}'. Call list_codes for the available codes.",
            )
        row = self._code_rows().get(document_id, {})
        version_date = _first_present(row, CODE_VERSION_COLUMNS)
        base = {
            "found": True,
            "code": document_id,
            "code_name": row.get("code_name"),
            "source_url": self._code_url(document_id),
            "version_date": version_date,
            "version_note": None if version_date else VERSION_UNKNOWN_NOTE,
        }
        articles = self._store.get_code_articles(document_id, chapter)
        chapters = self._chapters(articles) if not chapter else []
        if chapters:
            return CodeStructure(chapters=chapters, total_articles=len(articles), **base)
        limit = max(1, min(limit, MAX_BROWSE_LIMIT))
        page = articles[offset: offset + limit]
        message = None
        if offset + limit < len(articles):
            message = (
                f"Showing {len(page)} of {len(articles)}; "
                f"call again with offset={offset + limit}."
            )
        if not articles:
            message = f"No articles found in chapter '{chapter}'."
        return CodeStructure(
            articles=[
                ArticleRef(article_number=a["article_number"], article_title=a.get("article_title"))
                for a in page
            ],
            total_articles=len(articles),
            offset=offset,
            message=message,
            **base,
        )

    @staticmethod
    def _chapters(articles: list[dict[str, Any]]) -> list[ChapterSummary]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for a in articles:
            if a.get("chapter"):
                grouped.setdefault(a["chapter"], []).append(a)
        return [
            ChapterSummary(
                chapter=name,
                article_count=len(items),
                first_article=items[0]["article_number"],
                last_article=items[-1]["article_number"],
            )
            for name, items in grouped.items()
        ]

    def verify_citation(
        self, code: str, article: str, claim: str, paragraph: str | None = None
    ) -> VerifyCitationResult:
        """Does the cited article exist, and what does it actually say."""
        base = {"code": code, "article": article, "claim": claim, "paragraph_requested": paragraph}
        art = self._lookup(code, article, paragraph)
        if art is None:
            return VerifyCitationResult(
                exists=False, message=self._not_found_message(code, article), **base
            )
        text = art["content_ka"]
        paragraph_exists = None
        if paragraph:
            paragraph_exists = art.get("paragraph") is not None
            if paragraph_exists:
                text = art["paragraph"]["text"]
        message = "The article exists. Compare the claim with the text before relying on it."
        if art.get("is_repealed"):
            message = "The article is repealed (ამოღებულია). Do not rely on it as current law."
        elif paragraph and not paragraph_exists:
            message = f"The article exists, but paragraph {paragraph} is not in its stored text."
        return VerifyCitationResult(
            exists=True,
            paragraph_exists=paragraph_exists,
            is_repealed=art.get("is_repealed", False),
            article_number=art["article_number"],
            article_title=art.get("article_title"),
            text=text,
            source_url=self._article_url(art),
            lexical_check=self._lexical_check(claim, text),
            message=message,
            **self._version(art),
            **base,
        )

    @staticmethod
    def _lexical_check(claim: str, text: str) -> LexicalCheck:
        claim_numbers = list(dict.fromkeys(_NUMBER.findall(claim)))
        text_numbers = set(_NUMBER.findall(text))
        terms = {_stem(w) for w in _words(claim) if len(w) >= 4 and not w.isdigit()}
        lowered = text.lower()
        return LexicalCheck(
            numbers_in_claim=claim_numbers,
            numbers_found_in_text=[n for n in claim_numbers if n in text_numbers],
            numbers_not_in_text=[n for n in claim_numbers if n not in text_numbers],
            claim_terms_found=sum(1 for t in terms if t in lowered),
            claim_terms_total=len(terms),
        )

    # ── Court practice ───────────────────────────────────────

    def _court_client(self) -> ChromaClient | None:
        """The Chroma client when a court collection is loaded, else None."""
        if self._chroma is None:
            if not Path(settings.chroma_persist_dir).exists():
                return None
            self._chroma = get_chroma_client()
        if not any(c in self._chroma.available_collections for c in COURT_COLLECTIONS):
            return None
        return self._chroma

    def find_court_practice(self, query: str, limit: int = 5) -> CourtPracticeResult:
        """Real decisions whose text contains the query's key words, grouped by case."""
        limit = max(1, min(limit, 10))
        chroma = self._court_client()
        if chroma is None:
            return CourtPracticeResult(
                query=query, status="source_unavailable", results=[],
                message=(
                    "Court decisions are not available on this server. Say that no court "
                    "practice was checked; do not cite or describe any decision."
                ),
            )
        stems = sorted({_stem(w) for w in _words(query) if len(w) >= 5}, key=len, reverse=True)
        # Decisions matching more of the key words come first; fewer words
        # widen the net until enough decisions are found.
        chunks: list[dict[str, Any]] = []
        for size in (3, 2, 1):
            if not stems[:size]:
                break
            chunks += chroma.find_documents_containing(
                stems[:size], list(COURT_COLLECTIONS), limit * 4
            )
            if len(self._group_by_case(chunks)) >= limit:
                break
        decisions = self._group_by_case(chunks)[:limit]
        if not decisions:
            return CourtPracticeResult(
                query=query, status="none_found", results=[],
                message=(
                    "No court decision matched. Say so plainly; do not mention court practice "
                    "or invent case numbers."
                ),
            )
        return CourtPracticeResult(
            query=query, status="found", results=decisions,
            message="Quote only what the snippets say; cite the case number given.",
        )

    @staticmethod
    def _group_by_case(chunks: list[dict[str, Any]]) -> list[CourtDecision]:
        seen: dict[str, CourtDecision] = {}
        for chunk in chunks:
            meta = chunk.get("metadata") or {}
            case_id = str(meta.get("case_id") or "")
            collection = meta.get("_collection")
            if not case_id or collection not in COURT_COLLECTIONS:
                continue
            key = f"case:{collection}:{case_id}"
            if key in seen:
                continue
            url = meta.get("source_url") or meta.get("url") or meta.get("pdf_url")
            seen[key] = CourtDecision(
                id=key,
                case_number=str(meta.get("case_number") or case_id),
                court=COURT_NAMES[collection],
                collection=collection,
                date=str(meta["date"]) if meta.get("date") else None,
                year=str(meta["year"]) if meta.get("year") else None,
                category=meta.get("category"),
                snippet=_excerpt(chunk.get("content") or ""),
                source_url=str(url) if url else None,
                link_note=None if url else COURT_LINK_NOTE,
            )
        return list(seen.values())

    # ── ChatGPT search / fetch pair ──────────────────────────

    def search(self, query: str) -> SearchResults:
        """ChatGPT-compatible search: ids, titles and links of articles and decisions."""
        items = [
            SearchResultItem(
                id=hit.id,
                title=f"{hit.code_name}, {hit.article_number}"
                      + (f" — {hit.article_title}" if hit.article_title else ""),
                url=hit.source_url,
            )
            for hit in self.search_law(query, limit=8).results
        ]
        for decision in self.find_court_practice(query, limit=3).results:
            items.append(SearchResultItem(
                id=decision.id,
                title=f"{decision.court}, საქმე {decision.case_number}",
                url=decision.source_url or COURT_SITE_URL,
            ))
        return SearchResults(results=items)

    def fetch(self, id: str) -> FetchResult | None:
        """ChatGPT-compatible fetch: the full text behind a search result id."""
        kind, _, rest = id.partition(":")
        if kind == "article":
            code, _, article = rest.rpartition(":")
            result = self.get_article(code, article).article
            if result is None:
                return None
            return FetchResult(
                id=result.id,
                title=f"{result.code_name}, {result.article_number}"
                      + (f" — {result.article_title}" if result.article_title else ""),
                text=result.text,
                url=result.source_url,
                metadata={
                    k: v for k, v in {
                        "version_date": result.version_date,
                        "in_force_since": result.in_force_since,
                        "version_note": result.version_note,
                        "notice": result.notice,
                    }.items() if v
                },
            )
        if kind == "case":
            return self._fetch_case(rest)
        return None

    def _fetch_case(self, rest: str) -> FetchResult | None:
        collection, _, case_id = rest.partition(":")
        chroma = self._court_client()
        if chroma is None or collection not in COURT_COLLECTIONS:
            return None
        chunks = chroma.search_by_metadata({"case_id": case_id}, [collection], limit=200)
        if not chunks:
            return None
        chunks.sort(key=lambda c: (c.get("metadata") or {}).get("chunk_index", 0))
        decision = self._group_by_case(chunks)[0]
        return FetchResult(
            id=decision.id,
            title=f"{decision.court}, საქმე {decision.case_number}",
            text="\n\n".join(c.get("content") or "" for c in chunks),
            url=decision.source_url or COURT_SITE_URL,
            metadata={
                k: v for k, v in {
                    "date": decision.date,
                    "year": decision.year,
                    "link_note": decision.link_note,
                    "notice": decision.notice,
                }.items() if v
            },
        )


_connector_service: LawConnectorService | None = None


def get_law_connector_service() -> LawConnectorService:
    global _connector_service
    if _connector_service is None:
        _connector_service = LawConnectorService()
    return _connector_service
