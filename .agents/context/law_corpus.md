# Law Corpus Context

> **Status:** ✅ Complete — DO NOT MODIFY
> **Location:** `law_corpus/`
> **Last updated:** 2026-05-07

## ChromaDB Collections (3 sources)

| Collection | Chunks | Description | Status |
|------------|--------|-------------|--------|
| `georgian_laws` | 15,338 | 12 legal codes from matsne.gov.ge | ✅ Complete |
| `court_practice` | 5,197 | Supreme Court rulings (2022–2026) | ✅ Complete |
| `grand_chamber` | 177 | Grand Chamber binding decisions | ✅ Complete |
| **Total** | **20,712** | | |

All stored at `law_corpus/data/chroma/` with **768-dim vectors** via `gemini-embedding-001`.

## Querying

```python
import chromadb
client = chromadb.PersistentClient(path="<path>/law_corpus/data/chroma")

# Laws
laws = client.get_collection("georgian_laws")
results = laws.query(query_embeddings=[vec], n_results=50,
                     include=["documents", "metadatas", "distances"])

# Court Practice
court = client.get_collection("court_practice")
results = court.query(query_embeddings=[vec], n_results=50,
                      include=["documents", "metadatas", "distances"])

# Grand Chamber
gc = client.get_collection("grand_chamber")
results = gc.query(query_embeddings=[vec], n_results=50,
                   include=["documents", "metadatas", "distances"])
```

Query embeddings MUST use same model (gemini-embedding-001), 768 dims, `task_type=RETRIEVAL_QUERY`.

## Metadata Per Collection

### georgian_laws
`code_name`, `article_number`, `article_title`, `citation_text`, `source_url`, `article_url`, `document_number`

### court_practice
`case_id`, `category` (criminal/civil/administrative), `year`, `section`, `chunk_index`

### grand_chamber
`case_id`, `category`, `year`, `norm_interpreted`, `binding_rule`, `section`

## Legal Codes Indexed (georgian_laws)
Constitution, Civil Code, Criminal Code, Civil Procedure, Criminal Procedure, Administrative Code, Administrative Procedure, Administrative Offences, Labour Code, Tax Code, General Administrative Code, Juvenile Justice Code

## Evaluation Pipeline

Located at `eval/test_cases/`:
- **50 real cases** from Georgian Supreme Court rulings
- **holdout_eval.py** — removes/restores eval cases from ChromaDB to prevent contamination
- **run_eval.py** — LLM-as-judge evaluation (Gemini 3.1 Pro)
- **Scoring:** verdict_alignment, legal_reasoning, article_accuracy, practical_value (1–5)
- Results saved to `eval_results*.json` + per-case generations in `generations/evaluated/`

### Run Commands
```bash
# Holdout (remove eval cases from ChromaDB before testing)
python3 eval/test_cases/holdout_eval.py holdout

# Run eval on specific cases
python3 eval/test_cases/run_eval.py --cases "CASE1,CASE2" --output results.json

# Run by category
python3 eval/test_cases/run_eval.py --only criminal

# Restore (put eval cases back after testing)
python3 eval/test_cases/holdout_eval.py restore
```
