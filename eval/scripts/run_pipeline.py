#!/usr/bin/env python3
"""
🏛️ Fuzzzy Law — Evaluation Pipeline Runner

Feeds test cases (without expected outcomes) through the RAG pipeline sequentially,
respecting rate limits with exponential backoff.

Each case produces:
  eval/results/case_XXX/
    ├── case_input.json        — The case question (NO expected outcome)
    ├── ai_response.json       — Raw AI response from pipeline
    ├── expected_outcome.json  — Ground truth (for later comparison)
    └── metadata.json          — Timing, tokens, errors

Usage:
    python3 run_pipeline.py                           # Run all cases
    python3 run_pipeline.py --start 5 --end 10        # Run cases 5-10 only
    python3 run_pipeline.py --case-id CASE_001        # Run single case
    python3 run_pipeline.py --dry-run                 # Preview without running
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_ROOT = PROJECT_ROOT / "eval"
CASES_FILE = EVAL_ROOT / "test_cases" / "cases.json"
RESULTS_DIR = EVAL_ROOT / "results"
LAW_CORPUS_DIR = PROJECT_ROOT / "law_corpus"

# Add law_corpus to path so we can import poc_tester components
sys.path.insert(0, str(LAW_CORPUS_DIR))

# ── Rate Limiting Config ─────────────────────────────────────
# Gemini API: ~12 RPM for embedding, ~10 RPM for generation
# We use conservative limits to avoid 429s
MIN_DELAY_BETWEEN_CASES = 45    # seconds between full pipeline runs
MAX_RETRIES = 5                 # max retries per case
INITIAL_BACKOFF = 15            # seconds for first retry
MAX_BACKOFF = 300               # max 5 min backoff
BACKOFF_MULTIPLIER = 2.0        # exponential factor


def load_cases(cases_file: Path) -> list[dict]:
    """Load test cases from JSON file."""
    if not cases_file.exists():
        print(f"❌ Cases file not found: {cases_file}")
        print(f"   Run the case-gathering agent first to create this file.")
        print(f"   Prompt location: .agents/prompts/gather_real_cases.md")
        sys.exit(1)

    with open(cases_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # Validate
    for i, case in enumerate(cases):
        if "case_id" not in case:
            case["case_id"] = f"CASE_{i+1:03d}"
        if "user_question_ka" not in case:
            print(f"⚠️  Case {case['case_id']} missing 'user_question_ka' — skipping")

    return cases


def prepare_case_input(case: dict) -> dict:
    """Extract only the question part (no expected outcome) for the AI."""
    return {
        "case_id": case["case_id"],
        "category": case.get("category", "unknown"),
        "subcategory": case.get("subcategory", ""),
        "title_en": case.get("title_en", ""),
        "user_question_ka": case["user_question_ka"],
        "user_question_en": case.get("user_question_en", ""),
        "difficulty": case.get("difficulty", "unknown"),
    }


def prepare_expected_outcome(case: dict) -> dict:
    """Extract the ground truth for later comparison."""
    return {
        "case_id": case["case_id"],
        "applicable_laws": case.get("applicable_laws", []),
        "actual_outcome": case.get("actual_outcome", {}),
        "situation_description_ka": case.get("situation_description_ka", ""),
        "situation_description_en": case.get("situation_description_en", ""),
        "source_url": case.get("source_url", ""),
        "source_name": case.get("source_name", ""),
        "year": case.get("year", ""),
        "court_instance": case.get("court_instance", ""),
        "verification_notes": case.get("verification_notes", ""),
    }


def run_single_case(case: dict, case_dir: Path, dry_run: bool = False) -> dict:
    """Run a single case through the RAG pipeline with retry logic."""
    case_id = case["case_id"]
    question = case["user_question_ka"]

    # Save case input (no expected outcome)
    case_input = prepare_case_input(case)
    (case_dir / "case_input.json").write_text(
        json.dumps(case_input, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Save expected outcome (for later comparison)
    expected = prepare_expected_outcome(case)
    (case_dir / "expected_outcome.json").write_text(
        json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if dry_run:
        print(f"  🔍 [DRY RUN] Would process: {question[:80]}...")
        return {"status": "dry_run", "case_id": case_id}

    # Import the pipeline (lazy to avoid import errors during dry-run)
    from poc_tester import (
        expand_queries,
        vector_search,
        fulltext_search,
        merge_and_dedup,
        rerank,
        legal_analysis,
    )

    metadata = {
        "case_id": case_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "question_length": len(question),
        "retries": 0,
        "errors": [],
    }

    # Retry loop with exponential backoff
    for attempt in range(MAX_RETRIES):
        try:
            t0 = time.time()

            # Stage 0: Query Expansion
            print(f"  📎 Stage 0: Expanding queries...")
            expanded = expand_queries(question)
            metadata["expanded_queries"] = len(expanded)

            # Stage 1: Vector Search
            print(f"  🧲 Stage 1: Vector search ({len(expanded)} queries)...")
            vector_hits = vector_search(expanded)
            metadata["vector_hits"] = len(vector_hits)

            # Stage 2: Full-Text Search
            print(f"  📝 Stage 2: Full-text search...")
            ft_hits = fulltext_search(expanded)
            metadata["fulltext_hits"] = len(ft_hits)

            # Stage 3: Merge & Dedup
            print(f"  🔄 Stage 3: Merge & dedup...")
            merged = merge_and_dedup(vector_hits, ft_hits)
            metadata["merged_chunks"] = len(merged)

            # Stage 4: Rerank
            print(f"  ⚖️  Stage 4: Reranking...")
            top_chunks = rerank(question, merged, 20)
            metadata["reranked_chunks"] = len(top_chunks)

            # Stage 5: Legal Analysis
            print(f"  🧠 Stage 5: Legal analysis...")
            analysis = legal_analysis(question, top_chunks)

            elapsed = time.time() - t0
            metadata["elapsed_seconds"] = round(elapsed, 1)
            metadata["response_length"] = len(analysis)
            metadata["status"] = "success"
            metadata["completed_at"] = datetime.now(timezone.utc).isoformat()

            # Save AI response
            ai_response = {
                "case_id": case_id,
                "question": question,
                "response": analysis,
                "retrieved_chunks": [
                    {
                        "chunk_id": c.get("chunk_id", ""),
                        "code_name": c.get("metadata", {}).get("code_name", ""),
                        "article_number": c.get("metadata", {}).get("article_number", ""),
                        "article_title": c.get("metadata", {}).get("article_title", ""),
                        "distance": c.get("distance", 0),
                    }
                    for c in top_chunks
                ],
                "pipeline_stages": {
                    "expanded_queries": expanded,
                    "total_vector_hits": len(vector_hits),
                    "total_fulltext_hits": len(ft_hits),
                    "total_merged": len(merged),
                    "total_reranked": len(top_chunks),
                },
            }

            (case_dir / "ai_response.json").write_text(
                json.dumps(ai_response, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # Save metadata
            (case_dir / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(f"  ✅ Done in {elapsed:.1f}s, {len(analysis)} chars")
            return metadata

        except Exception as e:
            error_msg = f"Attempt {attempt+1}/{MAX_RETRIES}: {type(e).__name__}: {e}"
            print(f"  ⚠️  {error_msg}")
            metadata["errors"].append(error_msg)
            metadata["retries"] = attempt + 1

            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                backoff = min(INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ** attempt), MAX_BACKOFF)
                print(f"  ⏳ Rate limited — backing off {backoff:.0f}s...")
                time.sleep(backoff)
            elif attempt < MAX_RETRIES - 1:
                backoff = min(INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ** attempt), MAX_BACKOFF)
                print(f"  ⏳ Retrying in {backoff:.0f}s...")
                time.sleep(backoff)
            else:
                metadata["status"] = "failed"
                metadata["completed_at"] = datetime.now(timezone.utc).isoformat()
                metadata["final_error"] = traceback.format_exc()

                # Save failure metadata
                (case_dir / "metadata.json").write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                # Save empty AI response to indicate failure
                (case_dir / "ai_response.json").write_text(
                    json.dumps({
                        "case_id": case_id,
                        "question": question,
                        "response": f"[PIPELINE FAILED: {e}]",
                        "error": str(e),
                    }, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                return metadata


def run_all(
    cases_file: Path = CASES_FILE,
    results_dir: Path = RESULTS_DIR,
    start: int = 0,
    end: int | None = None,
    case_id: str | None = None,
    dry_run: bool = False,
):
    """Run evaluation pipeline for all (or selected) cases."""
    cases = load_cases(cases_file)

    if case_id:
        cases = [c for c in cases if c["case_id"] == case_id]
        if not cases:
            print(f"❌ Case '{case_id}' not found")
            sys.exit(1)
    else:
        cases = cases[start:end]

    total = len(cases)
    print(f"\n{'='*70}")
    print(f"🏛️  Fuzzzy Law — Evaluation Pipeline")
    print(f"{'='*70}")
    print(f"📊 Cases to process: {total}")
    print(f"📁 Results directory: {results_dir}")
    print(f"⏱️  Estimated time: {total * (MIN_DELAY_BETWEEN_CASES + 120) // 60} min")
    print(f"{'='*70}\n")

    results_summary = []

    for i, case in enumerate(cases, 1):
        cid = case["case_id"]
        case_num = int(cid.split("_")[1]) if "_" in cid else i
        case_dir = results_dir / f"case_{case_num:03d}"
        case_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'─'*60}")
        print(f"📋 [{i}/{total}] {cid}: {case.get('title_en', 'Untitled')}")
        print(f"   Category: {case.get('category', '?')} / {case.get('subcategory', '?')}")
        print(f"   Difficulty: {case.get('difficulty', '?')}")
        print(f"{'─'*60}")

        # Skip if already completed
        meta_file = case_dir / "metadata.json"
        if meta_file.exists():
            existing = json.loads(meta_file.read_text("utf-8"))
            if existing.get("status") == "success":
                print(f"  ⏭️  Already completed — skipping (use --force to rerun)")
                results_summary.append(existing)
                continue

        result = run_single_case(case, case_dir, dry_run=dry_run)
        results_summary.append(result)

        # Rate limiting delay between cases
        if i < total and not dry_run:
            print(f"  ⏳ Waiting {MIN_DELAY_BETWEEN_CASES}s before next case...")
            time.sleep(MIN_DELAY_BETWEEN_CASES)

    # Final summary
    print(f"\n\n{'='*70}")
    print(f"📊 PIPELINE RESULTS SUMMARY")
    print(f"{'='*70}")

    success = sum(1 for r in results_summary if r.get("status") == "success")
    failed = sum(1 for r in results_summary if r.get("status") == "failed")
    dry = sum(1 for r in results_summary if r.get("status") == "dry_run")
    skipped = sum(1 for r in results_summary if r.get("status") not in ("success", "failed", "dry_run"))

    print(f"  ✅ Success: {success}")
    print(f"  ❌ Failed:  {failed}")
    if dry:
        print(f"  🔍 Dry run: {dry}")
    if skipped:
        print(f"  ⏭️  Skipped: {skipped}")
    print(f"  📁 Results: {results_dir}")

    # Save summary
    summary_file = results_dir / "pipeline_summary.json"
    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": total,
        "success": success,
        "failed": failed,
        "results": results_summary,
    }
    summary_file.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  📄 Summary: {summary_file}")


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run Fuzzzy Law evaluation pipeline"
    )
    parser.add_argument(
        "--cases-file",
        type=Path,
        default=CASES_FILE,
        help=f"Path to cases JSON file (default: {CASES_FILE})",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        help=f"Path to results directory (default: {RESULTS_DIR})",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start index (0-based, inclusive)",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="End index (0-based, exclusive)",
    )
    parser.add_argument(
        "--case-id",
        type=str,
        default=None,
        help="Run a single case by ID (e.g., CASE_001)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without running the pipeline",
    )

    args = parser.parse_args()

    run_all(
        cases_file=args.cases_file,
        results_dir=args.results_dir,
        start=args.start,
        end=args.end,
        case_id=args.case_id,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
