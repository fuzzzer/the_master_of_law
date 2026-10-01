# Law Corpus Audit — Progress

> **Last updated:** 2026-05-24
> **Status:** Pipeline fixes complete, VPS remediation pending
> **Full results:** `.tasks/results/15_law_corpus_audit/`

## Milestone 1: Audit & Document All Issues
- [x] Audited all 15,718 chunks in `georgian_laws` for metadata issues
- [x] Audited 177 chunks in `grand_chamber` for `norm_interpreted` coverage
- [x] Identified 7 bugs across 5 files
- [x] Documented in `.tasks/results/15_law_corpus_audit/bugs_found.md`
- [x] ✅ Milestone 1 complete

## Milestone 2: Fix Pipeline — article_number Malformation
- [x] Root cause: `html_parser.py` fallback uses raw text as article_num
- [x] Fix: Added fallback regex `re.search(r"მუხლი\s*(\d+)", text)`
- [x] 3 regression tests in `TestArticleNumberFallback`
- [x] ✅ Milestone 2 complete

## Milestone 3: Fix Pipeline — code_name Canonicalization
- [x] Root cause: `ingest_thresholds.py` passes short-form from catalog
- [x] Fix: Added `_canonicalize_code_name()` mapping
- [x] 6 regression tests in `TestThresholdCodeNameCanonical`
- [x] ✅ Milestone 3 complete

## Milestone 4: Fix Backend — Citation Service
- [x] Root cause: CODE_NAMES unordered + missing codes + no abbreviations
- [x] Fix: Reordered longest-first, added საარჩევნო კოდექსი, added abbreviation map
- [x] Backend tests pass (436/436)
- [x] ✅ Milestone 4 complete

## Milestone 5: VPS Data Remediation
- [ ] Deploy updated code to VPS
- [ ] Run ChromaDB metadata fix script (Option A) or full re-ingestion (Option B)
- [ ] Verify 0 short-form code_names, 0 malformed article_numbers
- [ ] Guide in `.tasks/results/15_law_corpus_audit/vps_remediation.md`
- [ ] ✅ Milestone 5 complete

## Milestone 6: Fix Remaining Open Bugs
- [ ] Fix `extract_norm_interpretation` in court/chunker.py (Bug #6)
- [ ] Fix `law_browser_service.get_code()` filter key (Bug #7)
- [ ] Details in `.tasks/results/15_law_corpus_audit/remaining_work.md`
- [ ] ✅ Milestone 6 complete

---

## Blockers

- **Milestone 5** requires VPS SSH access + deployment
- **Milestone 6, Bug #6** requires Vertex AI API calls for re-embedding grand_chamber
