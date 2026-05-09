# Fixed! Now has backoff + resume support.

Run this:

```bash
cd /Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/law_corpus
source .venv/bin/activate
python3 ingest_thresholds.py
```

- Batches of 10 with 5s delay between
- Auto-retries on rate limit (exponential backoff: 20s, 40s, 80s...)
- Saves progress to `embedding_cache.json` — if it crashes, just re-run and it picks up where it left off
- After done, delete `data/thresholds/embedding_cache.json`
