# 🏛️ Master of Law — Evaluation Pipeline

> LLM-as-Judge evaluation: 50 real Georgian Supreme Court cases → AI legal analysis → scoring
> **Last updated:** 2026-05-07

## Architecture

```
eval/
├── test_cases/
│   ├── cases.json                ← 50 real Supreme Court cases
│   ├── holdout_eval.py           ← Remove/restore eval cases from ChromaDB
│   ├── run_eval.py               ← Run AI evaluation (LLM-as-judge)
│   ├── eval_results.json         ← Latest evaluation scores
│   ├── eval_results_v1.json      ← v1 baseline (17 cases)
│   ├── eval_results_v2_lowscoring.json  ← v2 re-eval of low-scoring
│   ├── holdout_backup.json       ← Backup of held-out embeddings
│   └── generations/
│       └── evaluated/            ← Per-case AI generation text files
├── steps.md                      ← Detailed run instructions
└── README.md                     ← This file
```

## Quick Start

```bash
# 1. Hold out eval cases from ChromaDB (prevents data contamination)
python3 eval/test_cases/holdout_eval.py holdout

# 2. Run evaluation (all cases)
python3 eval/test_cases/run_eval.py

# 2b. Or run specific cases only
python3 eval/test_cases/run_eval.py --cases "CRIM-1051ap-24,CRIM-311ap-23" --output results_v2.json

# 2c. Or run by category
python3 eval/test_cases/run_eval.py --only criminal

# 3. Restore eval cases after evaluation
python3 eval/test_cases/holdout_eval.py restore
```

## Scoring (1–5 per criterion)

| Criterion | Weight | What it measures |
|-----------|--------|-----------------|
| `verdict_alignment` | Core | Did AI predict the correct court outcome? |
| `legal_reasoning` | Core | Does AI's logic match the court's reasoning? |
| `article_accuracy` | Core | Did AI cite the correct law articles? |
| `practical_value` | Core | Would this advice help a real citizen? |
| `overall_score` | Composite | Weighted average of all criteria |

## ChromaDB Collections

```bash
# Verify all collections
cd law_corpus && python3 -c "
import chromadb
c = chromadb.PersistentClient(path='data/chroma')
for name in ['georgian_laws', 'court_practice', 'grand_chamber']:
    col = c.get_collection(name)
    print(f'{name}: {col.count()} chunks')
"
# Expected: georgian_laws: 15338, court_practice: 5197, grand_chamber: 177
```

## Key Features

- **Holdout system**: Eval cases removed from ChromaDB during testing → restored after
- **Crash-safe**: Results save after each case, auto-resume on restart
- **Per-case exports**: AI generations saved to `generations/evaluated/{case_id}.txt`
- **Targeted re-eval**: `--cases` flag for re-running specific low-scoring cases
- **Custom output**: `--output` flag to save to separate files (don't overwrite baselines)

See [steps.md](steps.md) for full detailed instructions.
