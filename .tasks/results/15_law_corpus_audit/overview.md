# Task #15: Law Corpus Audit — Overview

> **Last updated:** 2026-05-24
> **Status:** Pipeline fixes complete, VPS re-ingestion pending

## Purpose

Systematically audit and fix the law corpus ingestion pipeline to ensure all 20,712+ chunks in ChromaDB have correct, well-formed metadata — particularly `code_name` and `article_number` fields that the AI relies on for citation accuracy.

## Scope

This task covers the full data quality chain:

1. **Pipeline code fixes** — Fix root-cause bugs in the parsing/ingestion pipeline so future data is correct
2. **Citation service fixes** — Fix the backend code that extracts and verifies AI-generated law citations
3. **VPS data remediation** — Apply the fixes to the production VPS that has old (buggy) data
4. **Regression tests** — Ensure bugs don't come back

## What Was Found

7 bugs across 5 files (see [bugs_found.md](bugs_found.md) for full details):

| # | Severity | Component | Bug | Status |
|---|----------|-----------|-----|--------|
| 1 | 🔴 Critical | Pipeline: `html_parser.py` | Malformed article_number (60 chunks) | ✅ Fixed |
| 2 | 🔴 Critical | Pipeline: `ingest_thresholds.py` | Short-form code_name (20 chunks) | ✅ Fixed |
| 3 | 🔴 Critical | Backend: `citation_service.py` | Short form shadows long form | ✅ Fixed |
| 4 | 🟡 Medium | Backend: `citation_service.py` | Missing საარჩევნო კოდექსი | ✅ Fixed |
| 5 | 🟡 Medium | Backend: `citation_service.py` | No abbreviation support (სსკ, სკ) | ✅ Fixed |
| 6 | 🟡 Medium | Pipeline: `court/chunker.py` | extract_norm_interpretation broken | Open |
| 7 | 🟡 Medium | Backend: `law_browser_service.py` | get_code() uses wrong filter key | Open |

## Documents in This Directory

| File | Purpose |
|------|---------|
| `overview.md` | This file — summary and entry point |
| `bugs_found.md` | Detailed description of each bug with root cause analysis |
| `fixes_applied.md` | Exact code changes made, with diffs and rationale |
| `vps_remediation.md` | Step-by-step guide to fix the production VPS data |
| `remaining_work.md` | Open bugs and what needs to be done |
| `test_results.md` | Test suite status and regression test coverage |
