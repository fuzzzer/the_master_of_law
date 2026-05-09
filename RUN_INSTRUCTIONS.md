# BUGFIX: Marijuana had old+new values merged (5\n10 → now correctly "10")

Fixed newline-in-cell parsing for amended law values.
Must re-embed and re-ingest the corrected data.

```bash
cd /Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/law_corpus
source .venv/bin/activate

# Delete stale embedding cache so it re-embeds with corrected values
rm -f data/thresholds/embedding_cache.json

# Re-ingest (will re-embed all 380 entries)
python3 ingest_thresholds.py
```

After done, delete this file and `data/thresholds/embedding_cache.json`.
