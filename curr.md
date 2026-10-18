# 🏛️ Georgian Legal Evaluation Corpus — Build Status

## Current State

### ✅ What's Ready

| Component | Status | File |
|-----------|--------|------|
| Download script (65 verified URLs) | ✅ Ready to run | [download_cases.py](file:///Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/test_cases/download_cases.py) |
| Directory structure | ✅ Created | `eval/test_cases/raw/{supreme_court,constitutional_court}` |
| Pipeline architecture (steps.md) | ✅ Documented | [steps.md](file:///Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/steps.md) |
| Sample case schema | ✅ Exists | [sample_cases.json](file:///Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/test_cases/sample_cases.json) |

### 🔄 What Needs Your Action

| Step | Command | Notes |
|------|---------|-------|
| **1. Run downloader** | `python3 eval/test_cases/download_cases.py` | Requires internet; sandbox cannot reach `supremecourt.ge` |
| 2. Process PDFs | `python3 eval/test_cases/process_raw_cases.py` | Script to be created after download |
| 3. AI metadata extraction | `python3 eval/test_cases/extract_metadata.py` | Gemini-based, after text extraction |

---

## Download Script Details

### Files to Download: 65 total

| Source | Category | Count | Format | Years |
|--------|----------|-------|--------|-------|
| Supreme Court | Criminal | 12 PDFs | Quarterly collections | 2023-2025 |
| Supreme Court | Civil | 27 PDFs | **Monthly** collections | 2024-2026 |
| Supreme Court | Administrative | 12 PDFs | Quarterly collections | 2023-2025 |
| Constitutional Court | Individual cases | 9 HTML pages | Per-case decision | 2026 |
| Constitutional Court | Listing pages | 5 HTML pages | Index pages | All |

### Verified URL Patterns (from live page scraping)

```
Criminal:  supremecourt.ge/uploads/files/1/gamomtsemloba/collection/sisxli/sisxli-{range}-{year}.pdf
Civil:     supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-{month}-{year}.pdf
Admin:     supremecourt.ge/uploads/files/1/gamomtsemloba/collection/administraciuli/administraciuli-{range}-{year}.pdf
Const:     constcourt.ge/ka/judicial-acts?legal={case_id}
```

> [!IMPORTANT]
> Civil case URL patterns differ between years:
> - 2024-2026: `gamomtsemloba/collection/samoq/` (new path)
> - 2023: `gamotsemebi_des/` (old path)
> - Some 2024 files use the old path (e.g., samoq-10-2024)

### Constitutional Court Cases Identified

| Case ID | Number | Outcome | Description |
|---------|--------|---------|-------------|
| 19616 | №2/3/1609 | არ დაკმაყოფილდა | Pension age equality |
| 19615 | №1/2/1934 | Partially accepted | Shuragin property case |
| 19614 | №1/10/1912 | Not accepted, case terminated | Political party ban |
| 19617 | №1/9/1897 | Not accepted | Ombudsman vs Parliament |
| 19618 | №1/7/1485 | Not accepted, partially terminated | Ombudsman vs Parliament |
| 19613 | №1/8/1733 | Not accepted | Omega Motor Group vs Parliament |
| 19845 | N1961 | Pending | Abashidze vs Parliament |
| 19847 | N1962 | Pending | Kartvelishvili vs Parliament |
| 19823 | N1960 | Pending | Ilia University vs Parliament |

---

## Quick Start

```bash
cd /Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law

# See what will be downloaded
python3 eval/test_cases/download_cases.py --dry-run

# Download everything (needs internet)
python3 eval/test_cases/download_cases.py

# Download only criminal cases
python3 eval/test_cases/download_cases.py --only criminal

# Download only 2025 data
python3 eval/test_cases/download_cases.py --year 2025

# Download only constitutional court
python3 eval/test_cases/download_cases.py --only constitutional
```

## Next Steps After Download

1. **Verify download manifest** — check `raw/download_manifest.json` for failures
2. **Create PDF parser** — extract text from quarterly PDFs (each contains 10-30 cases)
3. **Create AI extractor** — Gemini processes extracted text to populate `cases.json`
4. **Run evaluation pipeline** — Steps 2-4 from [steps.md](file:///Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/steps.md)
