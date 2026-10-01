#!/usr/bin/env python3
"""
🏛️ Fuzzzy Law — Merge & Compare Results

Merges all evaluation case results into a single comparison document.
Produces structured comparison files for human/AI assessment.

Usage:
    python3 merge_results.py                          # Merge all
    python3 merge_results.py --format markdown        # Markdown report
    python3 merge_results.py --format json             # JSON (default)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────

EVAL_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = EVAL_ROOT / "results"
OUTPUT_DIR = EVAL_ROOT / "comparison"


def load_case_data(case_dir: Path) -> dict | None:
    """Load all data for a single case directory."""
    files = {
        "case_input": case_dir / "case_input.json",
        "ai_response": case_dir / "ai_response.json",
        "expected_outcome": case_dir / "expected_outcome.json",
        "metadata": case_dir / "metadata.json",
    }

    data = {"case_dir": str(case_dir.name)}

    for key, fpath in files.items():
        if fpath.exists():
            try:
                data[key] = json.loads(fpath.read_text("utf-8"))
            except json.JSONDecodeError:
                data[key] = {"error": f"Failed to parse {fpath.name}"}
        else:
            data[key] = None

    # Skip if no AI response
    if data.get("ai_response") is None:
        return None

    return data


def extract_cited_articles(response_text: str) -> list[str]:
    """Extract law article citations from AI response text."""
    # Match patterns like "მუხლი 120", "SSK მუხლი 53", etc.
    patterns = [
        r'მუხლი\s+(\d+)',                   # Georgian: მუხლი 120
        r'მუხ\.\s*(\d+)',                    # Abbreviated: მუხ. 120
        r'[Aa]rticle\s+(\d+)',               # English: Article 120
        r'(\d+)\s*-?ე?\s*მუხლი',             # Reversed: 120-ე მუხლი
    ]

    citations = set()
    for pattern in patterns:
        matches = re.findall(pattern, response_text)
        for m in matches:
            citations.add(f"მუხლი {m}")

    return sorted(citations)


def compare_single_case(case_data: dict) -> dict:
    """Compare AI response against expected outcome for a single case."""
    case_input = case_data.get("case_input", {})
    ai_resp = case_data.get("ai_response", {})
    expected = case_data.get("expected_outcome", {})
    metadata = case_data.get("metadata", {})

    ai_text = ai_resp.get("response", "")
    expected_outcome = expected.get("actual_outcome", {}) if expected else {}
    expected_laws = expected.get("applicable_laws", []) if expected else []

    # Extract cited articles from AI response
    ai_cited = extract_cited_articles(ai_text)

    # Extract expected article numbers
    expected_articles = set()
    for law in expected_laws:
        article = law.get("article", "")
        match = re.search(r'(\d+)', article)
        if match:
            expected_articles.add(f"მუხლი {match.group(1)}")

    # Calculate overlap
    ai_set = set(ai_cited)
    expected_set = expected_articles
    overlap = ai_set & expected_set
    missed = expected_set - ai_set
    extra = ai_set - expected_set

    comparison = {
        "case_id": case_input.get("case_id", "?"),
        "category": case_input.get("category", "?"),
        "subcategory": case_input.get("subcategory", "?"),
        "difficulty": case_input.get("difficulty", "?"),
        "title": case_input.get("title_en", "?"),

        "question_ka": case_input.get("user_question_ka", ""),
        "question_en": case_input.get("user_question_en", ""),

        "ai_response": ai_text,
        "ai_response_length": len(ai_text),

        "expected_verdict": expected_outcome.get("verdict", ""),
        "expected_sentence": expected_outcome.get("sentence", ""),
        "expected_sentence_en": expected_outcome.get("sentence_en", ""),
        "expected_reasoning": expected_outcome.get("key_reasoning", ""),

        "expected_articles": sorted(expected_articles),
        "ai_cited_articles": ai_cited,
        "articles_overlap": sorted(overlap),
        "articles_missed": sorted(missed),
        "articles_extra": sorted(extra),

        "article_recall": len(overlap) / len(expected_set) if expected_set else 0,
        "article_precision": len(overlap) / len(ai_set) if ai_set else 0,

        "pipeline_status": metadata.get("status", "unknown"),
        "pipeline_time_seconds": metadata.get("elapsed_seconds", 0),
        "pipeline_retries": metadata.get("retries", 0),

        "source_url": expected.get("source_url", "") if expected else "",
        "source_name": expected.get("source_name", "") if expected else "",
        "verification_notes": expected.get("verification_notes", "") if expected else "",
    }

    return comparison


def merge_all_results(
    results_dir: Path = RESULTS_DIR,
    output_dir: Path = OUTPUT_DIR,
    output_format: str = "json",
):
    """Merge all case results into comparison documents."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all case directories
    case_dirs = sorted(
        [d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("case_")],
        key=lambda d: d.name,
    )

    if not case_dirs:
        print(f"❌ No case directories found in {results_dir}")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"🏛️  Fuzzzy Law — Merge & Compare")
    print(f"{'='*70}")
    print(f"📁 Found {len(case_dirs)} case directories")

    comparisons = []
    for case_dir in case_dirs:
        data = load_case_data(case_dir)
        if data:
            comp = compare_single_case(data)
            comparisons.append(comp)
            status = "✅" if comp["pipeline_status"] == "success" else "❌"
            recall = comp["article_recall"]
            print(f"  {status} {comp['case_id']}: recall={recall:.0%}, {comp['ai_response_length']} chars")

    # ── JSON Output ──────────────────────────────────────────
    merged_json = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(comparisons),
        "summary": {
            "success": sum(1 for c in comparisons if c["pipeline_status"] == "success"),
            "failed": sum(1 for c in comparisons if c["pipeline_status"] == "failed"),
            "avg_response_length": (
                sum(c["ai_response_length"] for c in comparisons) // len(comparisons)
                if comparisons else 0
            ),
            "avg_article_recall": (
                sum(c["article_recall"] for c in comparisons) / len(comparisons)
                if comparisons else 0
            ),
            "avg_article_precision": (
                sum(c["article_precision"] for c in comparisons) / len(comparisons)
                if comparisons else 0
            ),
            "avg_pipeline_time": (
                sum(c["pipeline_time_seconds"] for c in comparisons) / len(comparisons)
                if comparisons else 0
            ),
            "by_category": {},
            "by_difficulty": {},
        },
        "cases": comparisons,
    }

    # Category breakdown
    for comp in comparisons:
        cat = comp["category"]
        if cat not in merged_json["summary"]["by_category"]:
            merged_json["summary"]["by_category"][cat] = {"count": 0, "avg_recall": 0}
        merged_json["summary"]["by_category"][cat]["count"] += 1
        merged_json["summary"]["by_category"][cat]["avg_recall"] += comp["article_recall"]

    for cat, data in merged_json["summary"]["by_category"].items():
        data["avg_recall"] = round(data["avg_recall"] / data["count"], 3) if data["count"] else 0

    # Difficulty breakdown
    for comp in comparisons:
        diff = comp["difficulty"]
        if diff not in merged_json["summary"]["by_difficulty"]:
            merged_json["summary"]["by_difficulty"][diff] = {"count": 0, "avg_recall": 0}
        merged_json["summary"]["by_difficulty"][diff]["count"] += 1
        merged_json["summary"]["by_difficulty"][diff]["avg_recall"] += comp["article_recall"]

    for diff, data in merged_json["summary"]["by_difficulty"].items():
        data["avg_recall"] = round(data["avg_recall"] / data["count"], 3) if data["count"] else 0

    json_out = output_dir / "full_comparison.json"
    json_out.write_text(
        json.dumps(merged_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n📄 JSON comparison: {json_out}")

    # ── Markdown Output ──────────────────────────────────────
    if output_format in ("markdown", "both"):
        md = generate_markdown_report(merged_json)
        md_out = output_dir / "full_comparison.md"
        md_out.write_text(md, encoding="utf-8")
        print(f"📄 Markdown report: {md_out}")

    # ── Per-case comparison files ────────────────────────────
    for comp in comparisons:
        case_id = comp["case_id"]
        case_num = int(case_id.split("_")[1]) if "_" in case_id else 0
        case_comp_file = output_dir / f"case_{case_num:03d}_comparison.json"
        case_comp_file.write_text(
            json.dumps(comp, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(f"\n✅ Merge complete! {len(comparisons)} cases compared.")
    print(f"📁 Output: {output_dir}")

    # Print summary table
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY")
    print(f"{'='*70}")
    print(f"{'Case ID':<12} {'Category':<14} {'Diff':<8} {'Recall':<8} {'Prec':<8} {'Time':<6}")
    print(f"{'─'*12} {'─'*14} {'─'*8} {'─'*8} {'─'*8} {'─'*6}")
    for c in comparisons:
        print(
            f"{c['case_id']:<12} {c['category']:<14} {c['difficulty']:<8} "
            f"{c['article_recall']:<8.0%} {c['article_precision']:<8.0%} "
            f"{c['pipeline_time_seconds']:<6.0f}s"
        )


def generate_markdown_report(data: dict) -> str:
    """Generate a markdown comparison report."""
    lines = [
        "# 🏛️ Fuzzzy Law — Evaluation Report",
        "",
        f"> Generated: {data['generated_at']}",
        f"> Total cases: {data['total_cases']}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Cases | {data['summary']['success'] + data['summary']['failed']} |",
        f"| Successful | {data['summary']['success']} |",
        f"| Failed | {data['summary']['failed']} |",
        f"| Avg Response Length | {data['summary']['avg_response_length']} chars |",
        f"| Avg Article Recall | {data['summary']['avg_article_recall']:.1%} |",
        f"| Avg Article Precision | {data['summary']['avg_article_precision']:.1%} |",
        f"| Avg Pipeline Time | {data['summary']['avg_pipeline_time']:.0f}s |",
        "",
        "## By Category",
        "",
        "| Category | Count | Avg Recall |",
        "|----------|-------|------------|",
    ]

    for cat, info in data["summary"]["by_category"].items():
        lines.append(f"| {cat} | {info['count']} | {info['avg_recall']:.1%} |")

    lines.extend([
        "",
        "## By Difficulty",
        "",
        "| Difficulty | Count | Avg Recall |",
        "|------------|-------|------------|",
    ])

    for diff, info in data["summary"]["by_difficulty"].items():
        lines.append(f"| {diff} | {info['count']} | {info['avg_recall']:.1%} |")

    lines.extend(["", "---", "", "## Case Details", ""])

    for comp in data["cases"]:
        lines.extend([
            f"### {comp['case_id']}: {comp['title']}",
            "",
            f"**Category:** {comp['category']} / {comp['subcategory']}  ",
            f"**Difficulty:** {comp['difficulty']}  ",
            f"**Status:** {comp['pipeline_status']}  ",
            f"**Time:** {comp['pipeline_time_seconds']}s  ",
            "",
            "#### Question (Georgian)",
            f"> {comp['question_ka']}",
            "",
            "#### Expected Outcome",
            f"- **Verdict:** {comp['expected_verdict']}",
            f"- **Sentence:** {comp['expected_sentence']}",
            f"- **Key Reasoning:** {comp['expected_reasoning']}",
            "",
            "#### Article Citation Analysis",
            f"- **Expected articles:** {', '.join(comp['expected_articles']) or 'N/A'}",
            f"- **AI cited articles:** {', '.join(comp['ai_cited_articles']) or 'N/A'}",
            f"- **Overlap:** {', '.join(comp['articles_overlap']) or 'None'}",
            f"- **Missed:** {', '.join(comp['articles_missed']) or 'None'}",
            f"- **Extra (hallucinated?):** {', '.join(comp['articles_extra']) or 'None'}",
            f"- **Recall:** {comp['article_recall']:.0%}",
            f"- **Precision:** {comp['article_precision']:.0%}",
            "",
            "#### AI Response (truncated)",
            "```",
            comp['ai_response'][:2000] + ("..." if len(comp['ai_response']) > 2000 else ""),
            "```",
            "",
            f"**Source:** [{comp['source_name']}]({comp['source_url']})",
            "",
            "---",
            "",
        ])

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Merge and compare evaluation results"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        help=f"Results directory (default: {RESULTS_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)",
    )

    args = parser.parse_args()
    merge_all_results(
        results_dir=args.results_dir,
        output_dir=args.output_dir,
        output_format=args.format,
    )


if __name__ == "__main__":
    main()
