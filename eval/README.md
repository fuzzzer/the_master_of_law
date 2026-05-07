# 🏛️ Master of Law — Evaluation Pipeline

> End-to-end quality assessment: real Georgian court cases → RAG pipeline → comparison → scoring

## Architecture

```
eval/
├── test_cases/
│   ├── cases.json             ← 30 real cases (from Step 1)
│   └── sample_cases.json      ← Template/schema reference
├── scripts/
│   ├── run_pipeline.py        ← Step 2: Feed cases through RAG
│   └── merge_results.py       ← Step 3: Merge & compare
├── results/
│   ├── case_001/
│   │   ├── case_input.json    ← Question only (no answer)
│   │   ├── ai_response.json   ← RAG pipeline output
│   │   ├── expected_outcome.json ← Ground truth
│   │   └── metadata.json      ← Timing, retries, errors
│   ├── case_002/
│   │   └── ...
│   └── pipeline_summary.json
├── comparison/
│   ├── full_comparison.json   ← All cases merged
│   ├── full_comparison.md     ← Markdown report
│   └── case_XXX_comparison.json ← Per-case comparisons
├── assessment/
│   ├── quality_report.json    ← AI agent scoring (from Step 4)
│   └── quality_report.md      ← Human-readable quality report
└── README.md                  ← This file
```

## 4-Step Process

### Step 1: Gather Real Cases 🔍
Copy the agent prompt and paste into a NEW Antigravity conversation:

```bash
cat .agents/prompts/gather_real_cases.md
```

The agent will search official Georgian court sources (supremecourt.ge, court.ge,
constcourt.ge, courtwatch.ge, gyla.ge) and produce `eval/test_cases/cases.json`
with 30 verified cases.

### Step 2: Run Pipeline 🚀
Feed cases through the RAG engine (respects rate limits, ~90 min for 30 cases):

```bash
cd law_corpus && source .venv/bin/activate

# Dry run first (no API calls)
python3 ../eval/scripts/run_pipeline.py --dry-run

# Run all cases
python3 ../eval/scripts/run_pipeline.py

# Run a subset
python3 ../eval/scripts/run_pipeline.py --start 0 --end 5

# Run single case
python3 ../eval/scripts/run_pipeline.py --case-id CASE_001
```

### Step 3: Merge & Compare 📊
Combine all results and calculate citation recall/precision:

```bash
python3 ../eval/scripts/merge_results.py --format both
```

### Step 4: Quality Assessment 🎯
Copy the assessment prompt and paste into a NEW Antigravity conversation:

```bash
cat .agents/prompts/assess_quality.md
```

The agent will read all comparison files and score each case on:
- **Legal Accuracy** (30%): Correct laws, interpretation, reasoning
- **Article Citation Recall** (20%): Expected articles found
- **Outcome Prediction** (20%): Matches actual court verdict
- **Practical Usefulness** (15%): Actionable advice, deadlines
- **Completeness** (15%): Defense strategies, counter-arguments, risks

## Rate Limiting Strategy

| Stage | API | Limit | Our Usage |
|-------|-----|-------|-----------|
| Query Expansion | Gemini generation | ~10 RPM | 1 call/case |
| Vector Search | Gemini embedding | ~12 RPM | 8-10 calls/case, 6s delay |
| Rerank | Gemini generation | ~10 RPM | 1 call/case |
| Legal Analysis | Gemini generation | ~10 RPM | 1 call/case |

- **Between cases:** 45s cooldown
- **On 429 error:** Exponential backoff (15s → 30s → 60s → 120s → 300s)
- **Max retries:** 5 per case
- **Resume:** Skips already-completed cases automatically

## Quick Health Check

```bash
# Verify ChromaDB is accessible
cd law_corpus && source .venv/bin/activate
python3 -c "import chromadb; c = chromadb.PersistentClient(path='data/chroma'); print(f'Chunks: {c.get_collection(\"georgian_laws\").count()}')"
# Should print: Chunks: 9450
```
