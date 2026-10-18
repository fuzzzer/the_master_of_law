"""Tests for threshold parsers — verified against real legal values."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.parser.narcotics_table_parser import DrugQuantityRow, parse_narcotics_pdf
from pipeline.parser.criminal_code_note_parser import parse_criminal_code_notes


PROJECT_ROOT = Path(__file__).parent.parent
NARCOTICS_PDF_DIR = PROJECT_ROOT.parent / ".assets"
CRIMINAL_CODE_JSON = PROJECT_ROOT / "data" / "georgian_laws" / "parsed" / "criminal_code.json"


def _find_narcotics_pdf() -> Path | None:
    pdfs = list(NARCOTICS_PDF_DIR.glob("ნარკოტიკული*"))
    return pdfs[0] if pdfs else None


NARCOTICS_PDF = _find_narcotics_pdf()
SKIP_PDF = NARCOTICS_PDF is None
SKIP_CC = not CRIMINAL_CODE_JSON.exists()


# -- Narcotics table parser --------------------------------------------------


@pytest.mark.skipif(SKIP_PDF, reason="Narcotics PDF not in .assets/")
class TestNarcoticsTableParser:

    @pytest.fixture(scope="class")
    def drug_rows(self) -> list[DrugQuantityRow]:
        assert NARCOTICS_PDF is not None
        return parse_narcotics_pdf(NARCOTICS_PDF)

    def _find(self, rows: list[DrugQuantityRow], name_fragment: str) -> DrugQuantityRow:
        matches = [r for r in rows if name_fragment in r.substance_ka]
        assert matches, f"No rows matching '{name_fragment}'"
        return matches[0]

    def _find_exact(self, rows: list[DrugQuantityRow], name: str) -> DrugQuantityRow:
        matches = [r for r in rows if r.substance_ka == name]
        assert matches, f"No rows with exact name '{name}'"
        return matches[0]

    def test_total_row_count_above_300(self, drug_rows: list[DrugQuantityRow]) -> None:
        assert len(drug_rows) > 300

    def test_has_both_sections(self, drug_rows: list[DrugQuantityRow]) -> None:
        sections = {r.section for r in drug_rows}
        assert sections == {"narcotics", "psychotropic"}

    def test_heroin_thresholds(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "ჰეროინი")
        assert row.small_grams == "0,005"
        assert row.large_grams == "0,2"
        assert row.extra_large_grams == "0,5"
        assert row.section == "narcotics"

    def test_cocaine_thresholds(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "კოკაინი")
        assert row.small_grams == "0,06"
        assert row.large_grams == "0,6"
        assert row.extra_large_grams == "2"

    def test_morphine_thresholds(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "მორფინი (ფუძე და მარილები)")
        assert row.small_grams == "0,04"
        assert row.large_grams == "0,4"
        assert row.extra_large_grams == "4"

    def test_fentanyl_thresholds(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find_exact(drug_rows, "ფენტანილი")
        assert row.small_grams == "0,0005"
        assert row.large_grams == "0,005"
        assert row.extra_large_grams == "0,05"
        assert row.section == "narcotics"

    def test_methadone_thresholds(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "მეთადონი (ფუძე და მარილები)")
        assert row.small_grams == "0,005"
        assert row.large_grams == "0,2"
        assert row.extra_large_grams == "1"

    def test_tramadol_thresholds(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "ტრამადოლი")
        assert row.small_grams == "1"
        assert row.large_grams == "80"
        assert row.extra_large_grams == "800"

    def test_amphetamine_thresholds(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "ამფეტამინი")
        assert row.small_grams == "0,005"
        assert row.large_grams == "0,1"
        assert row.extra_large_grams == "1"

    def test_codeine_thresholds(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "კოდეინი (ფუძე და მარილები)")
        assert row.small_grams == "0,2"
        assert row.large_grams == "2"
        assert row.extra_large_grams == "20"

    def test_mdma_thresholds(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "მდმა")
        assert row.small_grams == "0,05"
        assert row.large_grams == "0,5"
        assert row.extra_large_grams == "1"

    def test_desomorphine_thresholds(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "დეზომორფინი")
        assert row.small_grams == "0,001"
        assert row.large_grams == "0,01"
        assert row.extra_large_grams == "1"

    def test_diazepam_psychotropic(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "დიაზეპამი")
        assert row.section == "psychotropic"
        assert row.small_grams == "0,25"
        assert row.large_grams == "2,5"
        assert row.extra_large_grams == "25"

    def test_phenobarbital_psychotropic(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find_exact(drug_rows, "ფენობარბიტალი")
        assert row.section == "psychotropic"
        assert row.small_grams == "25"
        assert row.large_grams == "250"
        assert row.extra_large_grams == "500"

    def test_pregabalin_psychotropic(self, drug_rows: list[DrugQuantityRow]) -> None:
        row = self._find(drug_rows, "პრეგაბალინი")
        assert row.section == "psychotropic"
        assert row.small_grams == "0,6"

    def test_removed_entries_flagged(self, drug_rows: list[DrugQuantityRow]) -> None:
        removed = [r for r in drug_rows if r.is_removed]
        assert len(removed) > 0

    def test_undefined_quantity_substances_exist(self, drug_rows: list[DrugQuantityRow]) -> None:
        no_qty = [
            r for r in drug_rows
            if not r.is_removed
            and r.small_grams is None
            and r.large_grams is None
            and r.extra_large_grams is None
        ]
        assert len(no_qty) > 10


# -- Criminal Code note parser -----------------------------------------------


@pytest.mark.skipif(SKIP_CC, reason="criminal_code.json not found")
class TestCriminalCodeNoteParser:

    @pytest.fixture(scope="class")
    def thresholds(self) -> list:
        return parse_criminal_code_notes(CRIMINAL_CODE_JSON)

    def _find_article(self, thresholds: list, article_fragment: str):
        matches = [t for t in thresholds if article_fragment in t.article_number]
        assert matches, f"No thresholds for article '{article_fragment}'"
        return matches[0]

    def test_found_multiple_articles(self, thresholds: list) -> None:
        assert len(thresholds) >= 5

    def test_theft_large_amount(self, thresholds: list) -> None:
        theft = self._find_article(thresholds, "177")
        assert theft.thresholds.get("large_amount_lari") == 10_000

    def test_computer_crime_damage(self, thresholds: list) -> None:
        art = self._find_article(thresholds, "2861")
        assert art.thresholds.get("significant_damage_lari") == 150
        assert art.thresholds.get("large_amount_lari") == 10_000

    def test_timber_large_amount(self, thresholds: list) -> None:
        art = self._find_article(thresholds, "303")
        assert art.thresholds.get("large_amount_lari") == 3_000

    def test_trademark_large_amount(self, thresholds: list) -> None:
        art = self._find_article(thresholds, "196")
        assert art.thresholds.get("large_amount_lari") == 5000
