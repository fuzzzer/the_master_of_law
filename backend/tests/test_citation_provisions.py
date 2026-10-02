"""
A citation is verified only if the paragraph and sub-point it names exist
in that article — and are the ones that say what the sentence claims.

QA, 2026-10-01 (all marked `verified: true`):
  • pregnancy protection cited as Labour Code 47(1)(გ) — the rule is
    47(5)(გ); 47(1)(გ) is "completion of the work under the contract";
  • forced-absence pay cited as 48(4) — it is 48(9).
Verification checked that the ARTICLE existed. Extraction did not even read
"პუნქტი" (the Labour Code's word for paragraph), so the paragraph was lost.
"""

from __future__ import annotations

import pytest

from app.services.article_store_service import provision_text
from app.services.citation_service import CitationService, apply_provision_check

LABOUR = "საქართველოს შრომის კოდექსი"

# Art. 47 as the article store holds it: letters stored flat after the
# numbered paragraph they belong to.
ART_47 = [
    {"number": "1", "text": "შრომითი ხელშეკრულების შეწყვეტის საფუძვლებია:"},
    {"number": "ა", "text": "ეკონომიკური გარემოებები…"},
    {"number": "გ", "text": "შრომითი ხელშეკრულებით გათვალისწინებული სამუშაოს შესრულება;"},
    {"number": "2", "text": "ამ მუხლის პირველი პუნქტის „ზ“ და „თ“ ქვეპუნქტებით…"},
    {"number": "5", "text": "დაუშვებელია შრომითი ხელშეკრულების შეწყვეტა:"},
    {"number": "ა", "text": "სხვა საფუძვლით…"},
    {"number": "გ", "text": "დასაქმებული ქალის მიერ თავისი ორსულობის შესახებ დამსაქმებლისთვის შეტყობინებიდან…"},
]


@pytest.mark.parametrize("text, paragraph, sub_point", [
    (f"{LABOUR}ის 47-ე მუხლის მე-5 პუნქტის „გ“ ქვეპუნქტი", "5", "გ"),
    (f"{LABOUR}ის 47-ე მუხლის პირველი პუნქტის „გ“ ქვეპუნქტი", "1", "გ"),
    (f"{LABOUR}ის 47-ე მუხლის 1-ლი პუნქტის „გ“ ქვეპუნქტი", "1", "გ"),
    (f"{LABOUR}, მუხლი 47(5)(გ)", "5", "გ"),
    (f"{LABOUR}, მუხლი 47.5.გ", "5", "გ"),
    (f"{LABOUR}ის 48-ე მუხლის მე-9 პუნქტი", "9", ""),
    (f"{LABOUR}, მუხლი 48.9", "9", ""),
    (f"{LABOUR}, მუხლი 48(9)", "9", ""),
    (f"{LABOUR}ის 48-ე მუხლის მე-8 ნაწილი", "8", ""),
    (f"{LABOUR}, მუხლი 48", "", ""),
])
def test_the_paragraph_and_sub_point_are_read_in_every_form_the_codes_use(text, paragraph, sub_point):
    (c,) = CitationService().extract_citations(text)
    assert c["article_number"] in ("მუხლი 47", "მუხლი 48")
    assert (c["paragraph"], c["sub_point"]) == (paragraph, sub_point)


def test_each_citation_keeps_the_sentence_it_supports():
    text = (f"ხელფასი უნდა გადაგიხადონ. ორსულობის გამო გათავისუფლება აკრძალულია "
            f"({LABOUR}ის 47-ე მუხლის პირველი პუნქტის „გ“ ქვეპუნქტი). სხვა წინადადება.")
    (c,) = CitationService().extract_citations(text)
    assert c["claim"].startswith("ორსულობის გამო") and "სხვა წინადადება" not in c["claim"]


def test_a_sub_point_belongs_to_the_paragraph_above_it():
    assert "სამუშაოს შესრულება" in provision_text(ART_47, "1", "გ")
    assert "ორსულობის" in provision_text(ART_47, "5", "გ")
    assert provision_text(ART_47, "2", "გ") is None, "paragraph 2 has no sub-points"
    assert provision_text(ART_47, "9", "") is None


def _lookup(code, article):
    return ART_47 if article == "მუხლი 47" else None


def _cited(paragraph, sub_point=""):
    return {"code_name": LABOUR, "article_number": "მუხლი 47", "paragraph": paragraph,
            "sub_point": sub_point, "verified": True}


def test_a_paragraph_the_article_does_not_have_is_not_verified():
    (c,) = apply_provision_check([_cited("9")], _lookup)
    assert c["verified"] is False
    assert c["unverified_reason"] == "paragraph_not_found"


def test_a_sub_point_its_paragraph_does_not_have_is_not_verified():
    (c,) = apply_provision_check([_cited("2", "გ")], _lookup)
    assert c["verified"] is False
    assert c["unverified_reason"] == "sub_point_not_found"


def test_an_existing_provision_stays_verified_and_carries_its_text():
    (c,) = apply_provision_check([_cited("5", "გ")], _lookup)
    assert c["verified"] is True
    assert "ორსულობის" in c["provision_text"]


def test_a_provision_the_meaning_check_rejected_is_not_verified():
    """47(1)(გ) exists — only reading it shows it is about completed work,
    not pregnancy. The faithfulness pass names the citation it rejects."""
    (c,) = apply_provision_check([_cited("1", "გ")], _lookup, rejected={(LABOUR, "მუხლი 47", "1", "გ")})
    assert c["verified"] is False
    assert c["unverified_reason"] == "provision_does_not_support_claim"


@pytest.mark.asyncio
async def test_the_faithfulness_pass_reads_the_cited_provision_and_names_the_one_it_rejects():
    """No extra model call: the existing pass is given each cited
    provision's own text next to the sentence it is cited for."""
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.services.agent_pipeline_service import AgentPipelineService

    answer = (f"ორსულობის გამო გათავისუფლება აკრძალულია "
              f"({LABOUR}ის 47-ე მუხლის პირველი პუნქტის „გ“ ქვეპუნქტი).")
    chunk = {"chunk_id": "c", "content": "…", "metadata": {"code_name": LABOUR, "article_number": "მუხლი 47"}}
    gemini = MagicMock()
    gemini.generate_json = AsyncMock(return_value={"supported_count": 0, "general_count": 0, "unsupported": [
        {"statement": "ორსულობის გამო…", "reason": "47(1)(გ) is about completed work", "provision": "P1"}]})
    gemini.generate = AsyncMock(return_value="გასწორებული")
    store = MagicMock()
    store.get_article.side_effect = lambda code, article: {"paragraphs": ART_47} if article == "მუხლი 47" else None
    svc = AgentPipelineService(gemini=gemini, citation_svc=CitationService())

    with patch("app.services.agent_pipeline_service.get_article_store_service", return_value=store), \
            patch("app.services.agent_pipeline_service.record_step"):
        text, rejected = await svc._faithfulness_pass(answer, [chunk])

    prompt = gemini.generate_json.await_args.kwargs["prompt"]
    assert "[P1]" in prompt and "სამუშაოს შესრულება" in prompt, "the provision's own text is shown"
    assert [key[1:] for key in rejected] == [("მუხლი 47", "1", "გ")]
    assert gemini.generate_json.await_count == 1 and gemini.generate.await_count == 1, "no extra call"


def test_the_final_citations_describe_the_final_text():
    """Verification ran BEFORE the rewrite passes, so the `verified` list
    could describe text the user never saw. It is now taken from the text
    actually sent, with the provision check applied."""
    from unittest.mock import MagicMock, patch

    from app.services.agent_pipeline_service import AgentPipelineService

    text = f"{LABOUR}ის 47-ე მუხლის მე-9 პუნქტი ამბობს…"
    chunk = {"chunk_id": "c", "content": "…", "metadata": {"code_name": LABOUR, "article_number": "მუხლი 47"}}
    store = MagicMock()
    store.get_article.side_effect = lambda code, article: {"paragraphs": ART_47}
    svc = AgentPipelineService(gemini=MagicMock(), citation_svc=CitationService())

    with patch("app.services.agent_pipeline_service.get_article_store_service", return_value=store):
        (c,) = svc._checked_citations(text, [chunk])

    assert c["verified"] is False and c["unverified_reason"] == "paragraph_not_found"


def test_an_article_named_only_to_say_it_does_not_exist_is_not_a_citation():
    """QA, 2026-10-01: "Labour Code art. 500 does not exist" — correct —
    carried two `verified: false` citations, so the app warned on a right
    answer. Naming an article in order to deny it is not citing it."""
    from unittest.mock import MagicMock, patch

    from app.services.agent_pipeline_service import AgentPipelineService

    text = (f"{LABOUR}ის 500-ე მუხლი არ არსებობს — კოდექსში ამდენი მუხლი არ არის. "
            f"გათავისუფლების წესს {LABOUR}ის 48-ე მუხლი ადგენს.")
    chunk = {"chunk_id": "c", "content": "…", "metadata": {"code_name": LABOUR, "article_number": "მუხლი 48"}}
    store = MagicMock()
    store.get_article.side_effect = lambda code, article: None if "500" in article else {"paragraphs": []}
    svc = AgentPipelineService(gemini=MagicMock(), citation_svc=CitationService())

    with patch("app.services.agent_pipeline_service.get_article_store_service", return_value=store):
        cited = svc._checked_citations(text, [chunk])

    assert [c["article_number"] for c in cited] == ["მუხლი 48"]
