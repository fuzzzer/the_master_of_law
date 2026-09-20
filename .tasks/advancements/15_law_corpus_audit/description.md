# Law Corpus Audit & Repair

## Purpose

The law corpus is the foundation of the entire system — if articles can't be correctly retrieved by metadata, the AI gives wrong answers and real people's cases suffer. An audit of all 3 ChromaDB collections revealed **metadata inconsistencies** that degrade retrieval accuracy:

1. **`georgian_laws`** — 20 chunks have **short-form code names** (e.g. `სისხლის სამართლის კოდექსი` instead of `საქართველოს სისხლის სამართლის კოდექსი`). This breaks exact-match metadata searches and citation verification.

2. **`grand_chamber`** — Only 43/177 chunks have `binding_rule` populated. 0/177 have `norm_interpreted`. These fields are critical: Grand Chamber decisions are **binding** and override lower court interpretations. Without structured metadata, the system can't tell the AI *what* the binding rule is.

3. **`court_practice`** — Missing structured references to specific law articles cited in rulings. The text mentions articles (e.g. `177-ე მუხლის მე-2 ნაწილის`), but these aren't extracted into metadata, so the system can't cross-reference court decisions with specific law articles.

4. **Threshold catalog** — Some entries have `None` substance fields, causing `AttributeError` when searching.

## Dependencies

- Law corpus data at `law_corpus/data/` (all 3 collections)
- Ingestion pipeline at `law_corpus/pipeline/`
- ChromaDB 0.6.3

## Current Data State

| Collection | Chunks | Issues |
|-----------|--------|--------|
| `georgian_laws` | 15,718 | 20 chunks with short-form code_name (missing `საქართველოს` prefix) |
| `court_practice` | 4,618 | No structured article references in metadata |
| `grand_chamber` | 177 | `binding_rule` populated in 43/177; `norm_interpreted` in 0/177 |
| Threshold catalog | 380 | Some entries have `None` substance field |

---

## Milestones

### Milestone 1: Audit & Document All Issues

1. Write a diagnostic script (`law_corpus/scripts/audit_metadata.py`) that:
   - Scans all 3 collections
   - Reports missing/empty metadata fields per collection
   - Identifies short-form code names in `georgian_laws`
   - Counts `binding_rule` and `norm_interpreted` fill rates in `grand_chamber`
   - Finds `None` substances in threshold catalog
   - Outputs a structured JSON report

2. **Verify**: Run the script, save the report to `law_corpus/data/audit_report.json`.

---

### Milestone 2: Fix `georgian_laws` Code Name Inconsistencies

1. For the 20 chunks with short-form code names, update metadata to use full form:
   - `სისხლის სამართლის კოდექსი` → `საქართველოს სისხლის სამართლის კოდექსი`
   - `სამოქალაქო კოდექსი` → `საქართველოს სამოქალაქო კოდექსი`
   - `სისხლის სამართლის საპროცესო კოდექსი` → `საქართველოს სისხლის სამართლის საპროცესო კოდექსი`
   - `ადმინისტრაციულ სამართალდარღვევათა კოდექსი` → `საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი`
   - `შრომის კოდექსი` → `საქართველოს შრომის კოდექსი`

2. Use ChromaDB's `collection.update()` to patch metadata in-place.

3. **Verify**: Re-run audit script, confirm 0 short-form code names remain.

---

### Milestone 3: Enrich `grand_chamber` Metadata

1. For all 177 grand_chamber chunks, extract:
   - `norm_interpreted`: Which specific law article(s) the decision interprets (extract from document text using regex for `მუხლი \d+` patterns)
   - `binding_rule`: The binding legal principle (for the 134 chunks missing it, attempt extraction from the document text — look for ruling/resolution sections)

2. This should be done via a script (`law_corpus/scripts/enrich_grand_chamber.py`) that:
   - Reads each chunk's document text
   - Extracts article references → `norm_interpreted`
   - Extracts binding rules from resolution sections → `binding_rule`
   - Updates ChromaDB metadata in-place

3. **Verify**: Re-run audit, confirm `norm_interpreted` fill rate ≥ 80% and `binding_rule` fill rate ≥ 80%.

---

### Milestone 4: Fix Threshold Catalog

1. In `law_corpus/data/thresholds/threshold_catalog.json`:
   - Find entries with `null`/`None` substance fields
   - Either fill them from context or remove broken entries

2. **Verify**: `python -c "import json; d=json.load(open('...')); assert all(t.get('substance') is not None or t.get('threshold_type') != 'drug_quantity' for t in d['thresholds'])"` passes.

---

### Milestone 5: Update Ingestion Pipeline

1. Update `law_corpus/pipeline/court/chunker.py` to extract `norm_interpreted` during ingestion (so future re-ingestions preserve the fix).
2. Update `law_corpus/pipeline/config.py` code name mappings if they're the source of short-form names.
3. **Verify**: The pipeline code reflects the fixes, so re-running it wouldn't reintroduce the bugs.

---

### Milestone 6: Validation Tests

1. Run the backend test suite to make sure fixes don't break anything:
   ```bash
   cd backend && python -m pytest tests/ --ignore=tests/scripts -q
   ```

2. Write a quick smoke test that verifies the fixes hold:
   - `search_by_metadata(article_number="მუხლი 177", code_name="საქართველოს სისხლის სამართლის კოდექსი")` returns results
   - Grand chamber chunks have `norm_interpreted` populated
   - Threshold search for `მარიხუანა` works without errors

3. **Verify**: All tests pass, 0 failures.
