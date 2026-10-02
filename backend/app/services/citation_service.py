"""
Citation Service — extracts and verifies law citations from AI responses.

After Gemini generates a response, this service:
1. Extracts all law citations from the response text
2. Validates each citation exists in the corpus
3. Returns verified citations with full metadata
"""

from __future__ import annotations

import re
from typing import Callable, Any

from app.integrations.chroma_client import ChromaClient, get_chroma_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Pattern to match Georgian law citations. Handles both word orders, the
# common Georgian ordinal/superscript forms, and sub-article (paragraph)
# references:
#   "მუხლი 45", "მუხლი 177-ე", "მუხლი 115¹", "177-ე მუხლი", "177 მუხლი",
#   "მუხლი 48.8", "48-ე მუხლის მე-8 ნაწილი", "48-ე მუხლის პირველი ნაწილი".
# Group "num_after" captures the digits when the keyword precedes the number;
# group "num_before" captures them when the number precedes the keyword.
# Paragraph groups: "para_dot" (48.8), "para_paren" (48(8)), "para_me"
# (მე-8 ნაწილი/პუნქტი), "para_ord" (8-ე, 1-ლი), "para_word" (პირველი…).
# Sub-point groups: "sub_dot" (47.5.გ), "sub_paren" (47(5)(გ)), "sub_word"
# („გ“ ქვეპუნქტი). The codes say "ნაწილი" (Civil, Criminal) or "პუნქტი"
# (Labour) for a paragraph — reading only one of them lost the paragraph and
# let a wrong one pass as verified.
_ORDINAL_SUFFIX = r"(?:-[ა-ჰ]+)?"  # e.g. "-ე", "-ის"
_SUPERSCRIPT = r"[¹²³⁴⁵⁶⁷⁸⁹⁰]*"
_PARAGRAPH_WORDS = {
    "პირველ": "1", "მეორე": "2", "მესამე": "3", "მეოთხე": "4", "მეხუთე": "5",
    "მეექვსე": "6", "მეშვიდე": "7", "მერვე": "8", "მეცხრე": "9", "მეათე": "10",
}
_QUOTE = r"[„\"“”'«»]?"
_COMPACT_PROVISION = (
    r"(?:\.(?P<{p}dot>\d{{1,2}})(?!\d)(?:\.(?P<{s}dot>[ა-ჰ])(?![ა-ჰ]))?"
    r"|\((?P<{p}paren>\d{{1,2}})\)(?:\((?P<{s}paren>[ა-ჰ])\))?)?"
)
_PARAGRAPH_SUFFIX = (
    r"(?:\s+(?:მე-(?P<para_me>\d{1,2})|(?P<para_ord>\d{1,2})-(?:ე|ლი)"
    r"|(?P<para_word>" + "|".join(_PARAGRAPH_WORDS) + r")[ა-ჰ]*)\s+(?:ნაწილ|პუნქტ)[ა-ჰ]*"
    r"(?:\s+" + _QUOTE + r"(?P<sub_word>[ა-ჰ])" + _QUOTE + r"\s+ქვეპუნქტ[ა-ჰ]*)?)?"
)
ARTICLE_PATTERN = re.compile(
    r"მუხლი\s+(?P<num_after>\d+" + _SUPERSCRIPT + r")"
    + _COMPACT_PROVISION.format(p="para_", s="sub_") + _ORDINAL_SUFFIX
    + r"|(?P<num_before>\d+" + _SUPERSCRIPT + r")"
    + _COMPACT_PROVISION.format(p="para2_", s="sub2_") + _ORDINAL_SUFFIX
    + r"\s+მუხლ(?:ის|ი)" + _PARAGRAPH_SUFFIX,
    re.UNICODE,
)
_SENTENCE_END = re.compile(r"(?<=[.!?;])\s+|\n+")


def _claim_around(text: str, start: int, end: int) -> str:
    """The sentence a citation sits in — what the cited provision must back.

    A citation in brackets right after its sentence ("… აკრძალულია (მუხლი
    47).") belongs to that sentence, so the search runs from the citation's
    END backwards and forwards to the nearest sentence boundary.
    """
    begin = 0
    for m in _SENTENCE_END.finditer(text, 0, start):
        begin = m.end()
    tail = _SENTENCE_END.search(text, end)
    return text[begin:tail.start() if tail else len(text)].strip()


# Code names as they appear in the corpus (full "საქართველოს" prefix form).
# The model may output shorter forms — verify_citations handles both via normalization.
# IMPORTANT: Ordered longest first so _find_code_name picks the most specific match.
CODE_NAMES = [
    # Full canonical forms (longest — checked first)
    "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
    "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    "საქართველოს ადმინისტრაციული საპროცესო კოდექსი",
    "საქართველოს ზოგადი ადმინისტრაციული კოდექსი",
    "საქართველოს სამოქალაქო საპროცესო კოდექსი",
    "საქართველოს სისხლის სამართლის კოდექსი",
    "ნარკოტიკული საშუალებების შესახებ კანონი",
    "პერსონალურ მონაცემთა დაცვის შესახებ",
    "საქართველოს საგადასახადო კოდექსი",
    "საქართველოს საარჩევნო კოდექსი",
    "საქართველოს სამოქალაქო კოდექსი",
    "საქართველოს შრომის კოდექსი",
    "საქართველოს კონსტიტუცია",
    # Short forms the model commonly outputs (without "საქართველოს" prefix)
    "ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
    "სისხლის სამართლის საპროცესო კოდექსი",
    "ადმინისტრაციული საპროცესო კოდექსი",
    "ზოგადი ადმინისტრაციული კოდექსი",
    "სამოქალაქო საპროცესო კოდექსი",
    "სისხლის სამართლის კოდექსი",
    "საგადასახადო კოდექსი",
    "საარჩევნო კოდექსი",
    "სამოქალაქო კოდექსი",
    "შრომის კოდექსი",
    "კონსტიტუცია",
]

# Common abbreviations the model uses → canonical full name
_ABBREVIATION_MAP: dict[str, str] = {
    "სსკ": "საქართველოს სისხლის სამართლის კოდექსი",
    "სკ": "საქართველოს სამოქალაქო კოდექსი",
    "სსსკ": "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    "სსპკ": "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    "სპკ": "საქართველოს სამოქალაქო საპროცესო კოდექსი",
    "ზაკ": "საქართველოს ზოგადი ადმინისტრაციული კოდექსი",
    "ასდკ": "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
}

# Court case numbers as the model cites them: "ას-1280-2019", "ბს-922",
# "ას-449-431-2016", "814აპ-23", "2აგ-22" (optionally prefixed with №/საქმე).
CASE_NUMBER_PATTERN = re.compile(
    r"\b(?:ას|ბს|გს)-\d+(?:-\d+)*\b|\b\d+(?:აპ|აგ|კოლ|კ)-\d+\b",
    re.UNICODE,
)

# Pattern for abbreviation references like "სსკ-ის 177-ე მუხლი"
_ABBREV_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(_ABBREVIATION_MAP, key=len, reverse=True))
    + r")(?:-ი[სს]?)?\b",
    re.UNICODE,
)

_GEO_PREFIX = "საქართველოს "

# ── Anchored-claims protocol (grounding plan 2.2) ────────────────────────
# A paragraph making a normative legal assertion must carry an anchor —
# an article reference, a matsne link, or a court case number.
_LEGAL_CLAIM_PATTERN = re.compile(
    r"ითვალისწინებ|ეკისრება|ისჯება|ვალდებულ|უფლება აქვ|უფლებამოსილ"
    r"|აკრძალულ|ადგენს|განსაზღვრავს|ანაზღაურ|ჯარიმ|სასჯელ|პასუხისმგებლ"
    r"|კომპენსაცი|ეკუთვნ|ვადაში|ვადა |მოითხოვ",
    re.UNICODE,
)
_ANCHOR_PATTERN = re.compile(
    r"მუხლ|matsne\.gov\.ge|[აბ]ს-\d+(?:-\d+)?|№\s*\d|კოდექსი|კონსტიტუცი"
    r"|[„\"][^““\"]+[““\"]\s*(?:საქართველოს\s+)?კანონ",  # named law in quotes
    re.UNICODE,
)


def check_anchoring(text: str) -> dict[str, Any]:
    """Measure the unanchored legal-claim rate of a response.

    Splits the response into paragraphs/bullets; a paragraph containing a
    normative legal assertion counts as a claim. It is anchored when it — or
    its enclosing section (since the last markdown heading) — carries an
    article reference, matsne link, or case number, matching how the model
    structures answers (one citation covering the bullets under it).
    Flags only — no automatic stripping (mutilating legal advice is riskier
    than surfacing the metric for correction).
    """
    claims = 0
    unanchored = 0
    samples: list[str] = []
    section_anchored = False
    pending_claims: list[str] = []  # claims in this section awaiting an anchor
    for para in re.split(r"\n+", text):
        para = para.strip()
        if not para:
            continue
        if para.startswith("#"):
            # new section — flush claims of the finished, never-anchored section
            unanchored += len(pending_claims)
            samples.extend(pending_claims[: 5 - len(samples)])
            pending_claims = []
            section_anchored = False
            continue
        if _ANCHOR_PATTERN.search(para):
            section_anchored = True
            pending_claims = []
        if not _LEGAL_CLAIM_PATTERN.search(para):
            continue
        # advisory/meta paragraphs are not normative claims
        if para.startswith(("გირჩევთ", "რეკომენდაცია", "გთხოვთ", "⚠️", "**გაფრთხილება")):
            continue
        # lead-in paragraphs ending with ":" introduce a list whose items
        # carry the anchors — the claim lives in the (checked) items
        if para.endswith(":"):
            continue
        claims += 1
        if not section_anchored and not _ANCHOR_PATTERN.search(para):
            pending_claims.append(para[:200])
    unanchored += len(pending_claims)
    samples.extend(pending_claims[: 5 - len(samples)])
    return {
        "claim_paragraphs": claims,
        "unanchored": unanchored,
        "unanchored_rate": round(unanchored / claims, 3) if claims else 0.0,
        "unanchored_samples": samples,
    }


def _normalize_code_name(name: str) -> str:
    """Strip the 'საქართველოს' prefix for fuzzy matching."""
    return name.removeprefix(_GEO_PREFIX).strip()


class CitationService:
    """Extracts and verifies law citations from AI-generated text."""

    def __init__(self, chroma: ChromaClient | None = None):
        self._chroma = chroma

    @property
    def chroma(self) -> ChromaClient:
        if self._chroma is None:
            self._chroma = get_chroma_client()
        return self._chroma

    def extract_citations(self, text: str) -> list[dict[str, str]]:
        """Extract law citations from text."""
        citations = []

        # finditer gives the exact position of EACH reference, so the code name
        # is resolved relative to that reference (not the first match in the
        # text). This keeps two same-numbered articles from different codes
        # (e.g. Civil 177 and Criminal 177) mapped to their correct codes.
        for match in ARTICLE_PATTERN.finditer(text):
            article_num = match.group("num_after") or match.group("num_before")
            g = match.groupdict()
            paragraph = (
                g["para_dot"] or g["para_paren"] or g["para2_dot"] or g["para2_paren"]
                or g["para_me"] or g["para_ord"]
                or _PARAGRAPH_WORDS.get(g["para_word"] or "", "")
                or ""
            )
            sub_point = (
                g["sub_dot"] or g["sub_paren"] or g["sub2_dot"] or g["sub2_paren"]
                or g["sub_word"] or ""
            )
            code_name = self._find_code_name_preceding(text, match.start())
            citations.append({
                "article_number": f"მუხლი {article_num}",
                "paragraph": paragraph,
                "sub_point": sub_point,
                "claim": _claim_around(text, match.start(), match.end()),
                "code_name": code_name or "Unknown",
                "raw_text": f"{code_name}, მუხლი {article_num}" if code_name else f"მუხლი {article_num}",
            })

        # Deduplicate
        seen = set()
        unique = []
        for c in citations:
            key = (c["code_name"], c["article_number"], c["paragraph"], c["sub_point"])
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return unique

    def _find_code_name_preceding(self, text: str, start_pos: int) -> str | None:
        """Find the code name closest to and preceding the given position."""
        # Search backwards from the reference position for a known code name
        preceding = text[:start_pos]
        best_name = None
        best_pos = -1

        # Check abbreviations first (e.g. "სსკ-ის 177-ე მუხლი")
        for abbrev_m in _ABBREV_PATTERN.finditer(preceding):
            if abbrev_m.end() > best_pos:
                best_pos = abbrev_m.end()
                best_name = _ABBREVIATION_MAP[abbrev_m.group(1)]

        # Check full/short code names. CODE_NAMES is ordered longest-first,
        # so the first match at a given position is the most specific.
        for name in CODE_NAMES:
            pos = preceding.rfind(name)
            if pos > best_pos:
                best_pos = pos
                best_name = name

        return best_name

    def verify_citations(
        self,
        citations: list[dict[str, str]],
        retrieved_chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Verify extracted citations against retrieved corpus chunks.

        Builds a dual-key lookup: one under the full corpus code name and one
        under the normalized (no 'საქართველოს' prefix) form.  This handles the
        mismatch between what the model outputs (short form) and what the corpus
        stores (full form with prefix).

        Returns enriched citations with verification status and metadata.
        """
        chunk_lookup: dict[tuple[str, str], dict] = {}
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            full_code = meta.get("code_name", "")
            article = meta.get("article_number", "")
            normalized_code = _normalize_code_name(full_code)
            entry = {"content": chunk.get("content", ""), "metadata": meta}
            # Store under both full name and normalized (prefix-stripped) name
            for key in [(full_code, article), (normalized_code, article)]:
                if key not in chunk_lookup:
                    chunk_lookup[key] = entry

        verified = []
        for citation in citations:
            code = citation["code_name"]
            article = citation["article_number"]
            normalized = _normalize_code_name(code)
            # Try full name first, then normalized
            info = chunk_lookup.get((code, article)) or chunk_lookup.get((normalized, article))
            if info:
                verified.append({
                    **citation,
                    "verified": True,
                    "article_url": info["metadata"].get("article_url", ""),
                    "source_url": info["metadata"].get("source_url", ""),
                    "citation_text": info["metadata"].get("citation_text", ""),
                })
            else:
                verified.append({
                    **citation,
                    "verified": False,
                    "article_url": "",
                    "source_url": "",
                    "citation_text": "",
                })

        n_verified = sum(1 for v in verified if v["verified"])
        logger.info(
            "citations_verified",
            total=len(verified),
            verified=n_verified,
            unverified=len(verified) - n_verified,
        )
        return verified

    def verify_against_corpus(
        self,
        citations: list[dict[str, str]],
        already_retrieved: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Actively search the corpus for unverified citations.

        Unlike verify_citations() which only checks already-retrieved chunks,
        this method performs exact metadata searches in ChromaDB for any
        citations not found in the initial retrieval.

        Returns
        -------
        dict with keys:
            verified: Citations confirmed in already_retrieved chunks.
            corpus_found: Citations NOT in chunks but found via metadata search.
            not_found: Citations not in corpus at all (likely hallucinated).
        """
        chunk_lookup: dict[tuple[str, str], dict] = {}
        for chunk in already_retrieved:
            meta = chunk.get("metadata", {})
            full_code = meta.get("code_name", "")
            article = meta.get("article_number", "")
            normalized_code = _normalize_code_name(full_code)
            entry = {"content": chunk.get("content", ""), "metadata": meta}
            for key in [(full_code, article), (normalized_code, article)]:
                if key not in chunk_lookup:
                    chunk_lookup[key] = entry

        verified: list[dict[str, Any]] = []
        corpus_found: list[dict[str, Any]] = []
        not_found: list[dict[str, Any]] = []

        for citation in citations:
            code = citation["code_name"]
            article = citation["article_number"]
            normalized = _normalize_code_name(code)

            info = chunk_lookup.get((code, article)) or chunk_lookup.get((normalized, article))
            if info:
                verified.append({
                    **citation,
                    "verified": True,
                    "article_url": info["metadata"].get("article_url", ""),
                    "citation_text": info["metadata"].get("citation_text", ""),
                    "content": info["content"][:500],
                })
                continue

            corpus_hit = self._search_corpus_exact(article, code)
            if corpus_hit:
                corpus_found.append({
                    **citation,
                    "verified": True,
                    "article_url": corpus_hit["metadata"].get("article_url", ""),
                    "citation_text": corpus_hit["metadata"].get("citation_text", ""),
                    "content": corpus_hit.get("content", "")[:500],
                    "corpus_code_name": corpus_hit["metadata"].get("code_name", ""),
                })
            else:
                not_found.append({
                    **citation,
                    "verified": False,
                })

        logger.info(
            "citations_corpus_verified",
            verified=len(verified),
            corpus_found=len(corpus_found),
            not_found=len(not_found),
        )
        return {
            "verified": verified,
            "corpus_found": corpus_found,
            "not_found": not_found,
        }

    def extract_case_citations(self, text: str) -> list[str]:
        """Extract court case numbers cited in the response (plan 3.1)."""
        seen: set[str] = set()
        ordered: list[str] = []
        for m in CASE_NUMBER_PATTERN.finditer(text):
            num = m.group(0)
            if num not in seen:
                seen.add(num)
                ordered.append(num)
        return ordered

    def verify_case_citations(
        self, case_numbers: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        """Verify case numbers against court collections' metadata (plan 3.1).

        Returns {"verified": [...], "not_found": [...]} where verified entries
        carry the collection and case metadata.
        """
        verified: list[dict[str, Any]] = []
        not_found: list[dict[str, Any]] = []
        for num in case_numbers:
            try:
                hits = self.chroma.search_by_metadata(
                    where={"case_id": {"$eq": num}},
                    collections=["court_practice", "grand_chamber"],
                    limit=1,
                )
            except Exception as e:
                logger.warning("case_citation_lookup_failed", error=str(e))
                hits = []
            if hits:
                meta = hits[0].get("metadata", {})
                verified.append({
                    "case_number": num,
                    "collection": meta.get("_collection", ""),
                    "court": meta.get("court", ""),
                    "year": meta.get("year"),
                    "category": meta.get("category", ""),
                })
            else:
                not_found.append({"case_number": num})
        if case_numbers:
            logger.info(
                "case_citations_verified",
                total=len(case_numbers),
                verified=len(verified),
                not_found=len(not_found),
            )
        return {"verified": verified, "not_found": not_found}

    def _search_corpus_exact(
        self, article_number: str, code_name: str
    ) -> dict[str, Any] | None:
        """Search ChromaDB by exact article metadata."""
        if not article_number.startswith("მუხლი"):
            article_number = f"მუხლი {article_number.strip()}"

        where: dict[str, Any] = {"article_number": {"$eq": article_number}}
        if code_name and code_name != "Unknown":
            full_name = code_name if code_name.startswith("საქართველოს") else f"საქართველოს {code_name}"
            where = {"$and": [
                {"article_number": {"$eq": article_number}},
                {"$or": [
                    {"code_name": {"$eq": full_name}},
                    {"code_name": {"$eq": code_name}},
                ]},
            ]}

        try:
            hits = self.chroma.search_by_metadata(
                where=where,
                collections=["georgian_laws"],
                limit=3,
            )
            return hits[0] if hits else None
        except Exception as e:
            logger.warning("corpus_exact_search_failed", error=str(e))
            return None


_citation_service = None

ProvisionKey = tuple[str, str, str, str]  # (code_name, article_number, paragraph, sub_point)


def provision_key(citation: dict[str, Any]) -> ProvisionKey:
    return (
        citation.get("code_name", ""),
        citation.get("article_number", ""),
        citation.get("paragraph", ""),
        citation.get("sub_point", ""),
    )


def apply_provision_check(
    citations: list[dict[str, Any]],
    paragraphs_of: Callable[[str, str], list[dict] | None],
    rejected: set[ProvisionKey] | frozenset = frozenset(),
) -> list[dict[str, Any]]:
    """Withdraw `verified` from a citation whose paragraph or sub-point the
    article does not have, or whose provision the faithfulness pass found
    not to back its sentence; attach the provision's text to the rest.

    Articles without structured paragraphs are left as they are — there is
    nothing to check a paragraph against.
    """
    from app.services.article_store_service import provision_text

    checked = []
    for c in citations:
        c = dict(c)
        paragraph, sub_point = c.get("paragraph", ""), c.get("sub_point", "")
        paragraphs = paragraphs_of(c.get("code_name", ""), c.get("article_number", "")) if paragraph else None
        if paragraphs:
            text = provision_text(paragraphs, paragraph, sub_point)
            if text is None:
                c["verified"] = False
                c["unverified_reason"] = (
                    "sub_point_not_found"
                    if sub_point and provision_text(paragraphs, paragraph) is not None
                    else "paragraph_not_found"
                )
            else:
                c["provision_text"] = text
                if provision_key(c) in rejected:
                    c["verified"] = False
                    c["unverified_reason"] = "provision_does_not_support_claim"
        checked.append(c)
    return checked


def get_citation_service():
    global _citation_service
    if _citation_service is None:
        _citation_service = CitationService()
    return _citation_service
