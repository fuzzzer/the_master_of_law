# 🔄 Rebuild Law Corpus — Consolidated Versions

> **Why:** The previous corpus was scraped with `?publication=0` which returned
> the **original enactment text** instead of the latest consolidated version.
> All data (9,450 embeddings, ChromaDB, parsed docs) was built from outdated law text.

## Prerequisites

```bash
cd law_corpus
```

Make sure your `.env` has a valid `GOOGLE_API_KEY` (needed for Step 4 — embeddings).

---

## Step 1 — Scrape (download consolidated HTMLs from matsne.gov.ge)

```bash
python -m pipeline.main scrape
```

**Expected:** 15 documents scraped, each verified as `კონსოლიდირებული ვერსია (საბოლოო)`.
**Output:** `data/raw/html/*.html` + `data/raw/metadata/*.json`
**Time:** ~2 minutes (rate-limited at 2s per request)

---

## Step 2 — Parse (extract structured legal text from HTML)

```bash
python -m pipeline.main parse
```

**Expected:** 12–15 parsed documents with article counts.
**Output:** `data/parsed/*.json`
**Time:** ~30 seconds

---

## Step 3 — Chunk (split into embeddable pieces)

```bash
python -m pipeline.main chunk
```

**Expected:** ~9,000–12,000 chunks (varies with consolidated versions being larger).
**Output:** `data/chunks/*.json`
**Time:** ~30 seconds

---

## Step 4 — Embed (generate vector embeddings via Gemini)

```bash
python -m pipeline.main embed
```

**Expected:** All chunks get 768-dim embeddings.
**Output:** `data/embeddings/*.emb.json` + `data/embeddings/_cache_index.json`
**Time:** ~10–20 minutes (API rate-limited)

> ⚠️ If this step fails midway, it's **resumable** — just run it again.
> The embedder checkpoint tracks progress.

---

## Step 5 — Index (load into ChromaDB)

```bash
python -m pipeline.main index
```

**Expected:** All chunks indexed into ChromaDB with embeddings.
**Output:** `data/chroma/` (SQLite + binary files)
**Time:** ~1–2 minutes

---

## One-Shot (all steps at once)

If you prefer to run the entire pipeline in one go:

```bash
python -m pipeline.main run
```

---

## Verification

After completion, verify the corpus:

```bash
# Check stats
python -m pipeline.main stats

# Validate completeness (all P0 + P1 laws present)
python -m pipeline.main validate
```

---

## Full Nuke & Rebuild (if needed again)

If you ever need to start completely fresh:

```bash
# 1. Clear ALL data
rm -rf data/parsed/* data/chunks/* data/index/*
rm -rf data/raw/html/* data/raw/metadata/*
rm -rf data/checkpoints/*
rm -rf data/embeddings
mkdir -p data/embeddings
find data/chroma -mindepth 1 -delete

# 2. Run full pipeline
python -m pipeline.main run
```

---

## What Changed (Fix Summary)

| Before (broken) | After (fixed) |
|-----------------|---------------|
| `_to_consolidated_url` appended `?publication=0` | Strips `?publication=` param entirely |
| `publication=0` = **original** text (1995 Constitution!) | Base URL = **latest consolidated** version |
| No version verification | Checks for `კონსოლიდირებული ვერსია (საბოლოო)` label |
| Stale cache served silently | Cache auto-invalidated if non-consolidated |
