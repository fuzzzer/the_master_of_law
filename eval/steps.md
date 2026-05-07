# 🏛️ Evaluation Pipeline — Run Steps

> Evaluate the AI Legal Assistant against 50 real Georgian Supreme Court rulings.
> **Last updated:** 2026-05-07

**Approach:** Send case facts to AI → AI gives legal assessment → compare against actual court ruling → score quality.

---

## Step 1: Download & Process Court Cases ✅ DONE

### 1a. Download raw PDFs/HTML

```bash
python3 eval/test_cases/download_cases.py
```

**Result:** 79 PDFs + 9 HTML files → `eval/test_cases/raw/`

### 1b. Split PDFs into individual cases

```bash
python3 eval/test_cases/process_raw_cases.py
```

**Result:** 451 individual case files → `eval/test_cases/processed/`

### 1c. Convert Latin transliteration → Georgian Unicode

```bash
python3 eval/test_cases/convert_to_georgian.py
```

**Result:** All case files converted from AkadTrans Latin to proper ქართული

### 1d. Extract top 50 test cases

```bash
python3 eval/test_cases/extract_test_cases.py --top 50
```

**Result:** `eval/test_cases/cases.json` — 50 cases with:
- `situation` — facts section (input to AI)
- `court_reasoning` — court's legal analysis (ground truth)
- `court_resolution` — final ruling (ground truth)
- `verdict` — short verdict label

**Distribution:** 32 criminal, 15 civil, 3 administrative

---

## Step 2: Holdout Eval Cases ✅ DONE

**CRITICAL:** Before running evaluations, hold out the eval cases from ChromaDB to prevent data contamination.

```bash
# Remove eval cases from ChromaDB (saves backup to holdout_backup.json)
python3 eval/test_cases/holdout_eval.py holdout

# Check status
python3 eval/test_cases/holdout_eval.py status

# Restore after evaluation is complete
python3 eval/test_cases/holdout_eval.py restore
```

**Safety:** The holdout script saves backup to disk BEFORE deleting any chunks. If the process crashes, you can always restore from `holdout_backup.json`.

---

## Step 3: Run AI Evaluation ✅ DONE

```bash
# Auth: uses application default credentials (billed to GCP console)
# Defaults to: ~/.config/gcloud/application_default_credentials.json

# Test on 3 cases first
python3 eval/test_cases/run_eval.py --limit 3

# Run all 50 cases
python3 eval/test_cases/run_eval.py

# Run only criminal cases
python3 eval/test_cases/run_eval.py --only criminal

# Run specific cases only (comma-separated IDs)
python3 eval/test_cases/run_eval.py --cases "CRIM-1051ap-24,CRIM-311ap-23"

# Save to custom output file
python3 eval/test_cases/run_eval.py --cases "CASE1,CASE2" --output eval_results_v2.json

# Use a specific model
python3 eval/test_cases/run_eval.py --model gemini-2.5-flash

# Resume if interrupted (auto-skips completed)
python3 eval/test_cases/run_eval.py
```

**What happens per case:**
1. **AI Legal Advisor** receives `situation` text (case facts only, no ruling)
2. AI produces legal assessment: applicable laws, predicted outcome, reasoning
3. **AI Judge** compares the assessment against actual court ruling
4. Scores on 4 criteria (1-5 each):
   - `verdict_alignment` — did AI predict the correct outcome?
   - `legal_reasoning` — does AI's logic match the court's?
   - `article_accuracy` — did AI cite the right laws?
   - `practical_value` — would this help a real citizen?
5. **Generation saved** to `generations/evaluated/{case_id}.txt`

**Output:** `eval/test_cases/eval_results.json` (or custom `--output`)

> ⏱️ ~2 API calls per case × 50 cases ≈ 15-25 min (with rate limit pauses)
> 💾 Results save after each case — safe to interrupt and resume
> 📁 Each AI generation saved separately in `generations/evaluated/`

---

## Step 4: Review Results

After Step 3 completes, the script prints a summary report:

```
📊 EVALUATION REPORT
  Total evaluated: 50

  📈 Average Scores (1-5):
    verdict_alignment    : 3.80 ███░░
    legal_reasoning      : 3.60 ███░░
    article_accuracy     : 3.40 ███░░
    practical_value      : 4.00 ████░
    overall_score        : 3.70 ███░░

  📁 By category:
    criminal            : 3.85 (32 cases)
    civil               : 3.60 (15 cases)
    ...
```

**Detailed results** are in `eval/test_cases/eval_results.json`:

| What you want to know | Where |
|----------------------|-------|
| Overall scores | `eval_results.json` → `avg_*` fields |
| Per-case scores | `eval_results.json` → `results[].scores` |
| AI's actual response | `generations/evaluated/{case_id}.txt` |
| Weakest category | `eval_results.json` → compare `avg_*` by category |
| Judge's explanation | `eval_results.json` → `results[].scores.explanation` |

---

## Step 5: Restore Holdout ⚠️ ALWAYS DO THIS

```bash
python3 eval/test_cases/holdout_eval.py restore
```

This puts all eval cases back into ChromaDB so the production system has the full corpus.

---

## File Structure

```
eval/test_cases/
├── download_cases.py           ← Step 1a: download PDFs/HTML
├── process_raw_cases.py        ← Step 1b: split into individual cases
├── convert_to_georgian.py      ← Step 1c: Latin → Georgian Unicode
├── extract_test_cases.py       ← Step 1d: build cases.json
├── holdout_eval.py             ← Step 2: manage eval case holdout
├── run_eval.py                 ← Step 3: run AI evaluation
├── cases.json                  ← 50 test cases (committed)
├── eval_results.json           ← evaluation scores (generated)
├── eval_results_v1.json        ← v1 baseline (17 cases)
├── eval_results_v2_lowscoring.json ← v2 re-eval of low-scoring cases
├── holdout_backup.json         ← backup of held-out chunk data
├── generations/
│   └── evaluated/              ← per-case AI generation text files
│       ├── CRIM-1051ap-24.txt
│       └── ...
├── raw/                        ← downloaded PDFs (gitignored)
└── processed/                  ← split case files (gitignored)
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No GOOGLE_API_KEY` | `export GOOGLE_API_KEY="..."` or add to `backend/.env` |
| `429 rate limit` | Script handles this with auto-retry + backoff |
| Crashed mid-run | Just re-run — skips already-completed cases |
| Want to re-evaluate a case | Use `--output new_file.json` with `--cases` filter |
| Mixed Latin/Georgian text | Re-run `convert_to_georgian.py` then re-extract |
| Too few admin cases | `extract_test_cases.py --min-score 30 --top 60` |
| Missing 517 chunks | Run `restore_missing_chunks.py` (targeted delta re-embed) |
| numpy serialization error | Fixed in holdout_eval.py (save-before-delete) |
