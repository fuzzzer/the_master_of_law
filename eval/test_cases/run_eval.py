#!/usr/bin/env python3
"""
Evaluate the AI Legal Assistant against real Georgian Supreme Court rulings.

Flow per case:
  1. Send case SITUATION to AI → AI gives its legal assessment
  2. AI acts as a JUDGE → compares its own assessment vs actual court ruling
  3. Score alignment (1-5) + reasoning

Uses Vertex AI (Gemini) — billed through GCP console.

Usage:
  # Run full evaluation (all 50 cases)
  python3 run_eval.py

  # Test on first 3 cases
  python3 run_eval.py --limit 3

  # Only a specific category
  python3 run_eval.py --only criminal

  # Resume from a specific case
  python3 run_eval.py --resume-from CRIM-943ap-24

Auth:
  Uses application default credentials from GCP_SA_KEY_PATH or
  GOOGLE_APPLICATION_CREDENTIALS. Reads project/location from backend/.env.

Required:
  pip install google-genai
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent.parent
CASES_FILE = BASE_DIR / "cases.json"
RESULTS_FILE = BASE_DIR / "eval_results.json"

# ── Auth: set credentials path before any Google imports ──
GCP_SA_KEY_PATH = os.environ.get(
    "GCP_SA_KEY_PATH",
    os.path.expanduser("~/.config/gcloud/application_default_credentials.json"),
)
if os.path.exists(GCP_SA_KEY_PATH):
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", GCP_SA_KEY_PATH)

# Load backend .env for project config
env_file = PROJECT_ROOT / "backend" / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"'))

# GCP config from backend/.env
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0225498420")
GCP_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

# ─────────────────────────────────────────────
# Gemini client setup (Vertex AI)
# ─────────────────────────────────────────────

def get_gemini_client():
    """Initialize Gemini client via Vertex AI."""
    try:
        from google import genai
    except ImportError:
        print("ERROR: pip install google-genai")
        sys.exit(1)

    print(f"  Project:  {GCP_PROJECT}")
    print(f"  Location: {GCP_LOCATION}")
    print(f"  Creds:    {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'ADC')}")

    return genai.Client(
        vertexai=True,
        project=GCP_PROJECT,
        location=GCP_LOCATION,
    )


# ─────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────

LEGAL_ADVISOR_SYSTEM = """თქვენ ხართ საქართველოს სამართლის ექსპერტი AI ასისტენტი.
თქვენი ამოცანაა გააანალიზოთ წარმოდგენილი საქმის ფაქტობრივი გარემოებები და მისცეთ სამართლებრივი შეფასება.

თქვენ უნდა:
1. განსაზღვროთ რომელი კანონის რომელი მუხლები გამოიყენება
2. შეაფასოთ რა სამართლებრივი შედეგი მოჰყვება ფაქტობრივ გარემოებებს
3. იწინასწარმეტყველოთ სავარაუდო სასამართლო გადაწყვეტილება
4. მიუთითოთ ძლიერი და სუსტი მხარეები

გთხოვთ, პასუხი მისცეთ ქართულ ენაზე. იყავით კონკრეტული და მიუთითეთ ზუსტი მუხლის ნომრები."""

LEGAL_ADVISOR_PROMPT = """გთხოვთ, გააანალიზოთ შემდეგი საქმის ფაქტობრივი გარემოებები და მისცეთ სამართლებრივი შეფასება:

--- საქმის ფაქტები ---
{situation}
--- საქმის ფაქტები დასრულდა ---

გთხოვთ, მიუთითოთ:
1. გამოსაყენებელი სამართლის ნორმები (კანონი, მუხლი)
2. თქვენი სამართლებრივი შეფასება
3. სავარაუდო სასამართლო გადაწყვეტილება (საკასაციო საჩივარი დაკმაყოფილდება თუ არა?)
4. თქვენი დასკვნა"""

JUDGE_SYSTEM = """თქვენ ხართ სამართლებრივი ანალიზის ხარისხის შემფასებელი.
თქვენ მოცემული გაქვთ:
- AI ასისტენტის სამართლებრივი შეფასება საქმეზე
- ფაქტობრივი სასამართლო გადაწყვეტილება იმავე საქმეზე

შეაფასეთ AI ასისტენტის პასუხის ხარისხი."""

JUDGE_PROMPT = """შეადარეთ AI ასისტენტის სამართლებრივი შეფასება რეალურ სასამართლო გადაწყვეტილებასთან.

--- AI ასისტენტის შეფასება ---
{ai_response}
--- AI შეფასება დასრულდა ---

--- ფაქტობრივი სასამართლო გადაწყვეტილება ---
ვერდიქტი: {verdict}

სასამართლოს მსჯელობა (მოკლედ): {court_reasoning}

სარეზოლუციო ნაწილი: {court_resolution}
--- სასამართლო გადაწყვეტილება დასრულდა ---

შეაფასეთ AI ასისტენტის პასუხი შემდეგი კრიტერიუმებით (1-5 ქულა თითოეულზე):

1. **verdict_alignment** (ვერდიქტის თანხვედრა): AI-მ სწორად იწინასწარმეტყველა სასამართლოს გადაწყვეტილება?
   - 5 = ზუსტად იგივე დასკვნა
   - 4 = არსებითად სწორი, მცირე განსხვავებებით
   - 3 = ნაწილობრივ სწორი
   - 2 = ძირითადად არასწორი
   - 1 = სრულად არასწორი

2. **legal_reasoning** (სამართლებრივი მსჯელობა): AI-ს სამართლებრივი არგუმენტაცია რამდენად ემთხვევა სასამართლოს?
   - 5 = იგივე სამართლებრივი ლოგიკა
   - 4 = ძირითადად სწორი მსჯელობა
   - 3 = ნაწილობრივ სწორი
   - 2 = ძირითადად არასწორი ლოგიკა
   - 1 = სრულად არასწორი

3. **article_accuracy** (მუხლების სიზუსტე): AI-მ სწორი სამართლის ნორმები მიუთითა?
   - 5 = ყველა ძირითადი მუხლი სწორად
   - 4 = უმეტესობა სწორი
   - 3 = ნახევარი სწორი
   - 2 = ცოტა სწორი
   - 1 = არცერთი სწორი

4. **practical_value** (პრაქტიკული ღირებულება): AI-ს რჩევა რამდენად სასარგებლო იქნებოდა მოქალაქისთვის?
   - 5 = ძალიან სასარგებლო
   - 4 = საკმაოდ სასარგებლო
   - 3 = ზომიერად სასარგებლო
   - 2 = ნაკლებად სასარგებლო
   - 1 = უსარგებლო ან მავნე

უპასუხეთ **მხოლოდ** შემდეგი JSON ფორმატით, არაფერი სხვა:
{{
  "verdict_alignment": <1-5>,
  "legal_reasoning": <1-5>,
  "article_accuracy": <1-5>,
  "practical_value": <1-5>,
  "overall_score": <1-5>,
  "explanation": "<მოკლე ახსნა ქართულად, 2-3 წინადადება>"
}}"""


# ─────────────────────────────────────────────
# Evaluation logic
# ─────────────────────────────────────────────

def truncate_text(text: str, max_chars: int = 15000) -> str:
    """Truncate text to fit within context limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... ტექსტი შემოკლებულია ...]"


def call_gemini(client, system: str, prompt: str, model: str = "gemini-3.1-pro-preview",
                max_retries: int = 3) -> str:
    """Call Gemini API with retries."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "system_instruction": system,
                    "temperature": 0.3,
                    "max_output_tokens": 4096,
                },
            )
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait = (attempt + 1) * 15
                print(f"    ⏳ Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    ❌ Error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    return f"ERROR: {e}"
    return "ERROR: Max retries exceeded"


def parse_judge_response(text: str) -> dict:
    """Parse the judge's JSON response."""
    import re
    # Find JSON in the response
    json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: try to extract scores manually
    scores = {}
    for key in ["verdict_alignment", "legal_reasoning", "article_accuracy",
                 "practical_value", "overall_score"]:
        match = re.search(rf'"{key}":\s*(\d)', text)
        if match:
            scores[key] = int(match.group(1))

    if scores:
        scores.setdefault("explanation", "Could not parse full response")
        return scores

    return {
        "verdict_alignment": 0, "legal_reasoning": 0,
        "article_accuracy": 0, "practical_value": 0,
        "overall_score": 0, "explanation": "Failed to parse judge response",
        "raw_response": text[:500],
    }


def evaluate_case(client, case: dict, case_num: int, total: int,
                  model: str = "gemini-3.1-pro-preview") -> dict:
    """Run full evaluation on a single case."""
    case_id = case["case_id"]
    print(f"\n  [{case_num}/{total}] {case_id} ({case['category']})")

    # Step 1: Get AI legal assessment
    situation = truncate_text(case["situation"], 15000)
    prompt = LEGAL_ADVISOR_PROMPT.format(situation=situation)

    print(f"    📤 Sending situation ({len(situation):,} chars) to AI...")
    ai_response = call_gemini(client, LEGAL_ADVISOR_SYSTEM, prompt, model=model)

    if ai_response.startswith("ERROR"):
        print(f"    ❌ AI response failed: {ai_response[:100]}")
        return {"case_id": case_id, "status": "error", "error": ai_response}

    print(f"    📥 AI response: {len(ai_response):,} chars")

    # Step 2: Judge compares AI vs actual court ruling
    court_reasoning = truncate_text(case.get("court_reasoning", ""), 5000)
    court_resolution = truncate_text(case.get("court_resolution", ""), 3000)
    verdict = case.get("verdict", "unknown")

    judge_prompt = JUDGE_PROMPT.format(
        ai_response=truncate_text(ai_response, 5000),
        verdict=verdict,
        court_reasoning=court_reasoning,
        court_resolution=court_resolution,
    )

    print(f"    ⚖️  Judging AI response vs court ruling...")
    judge_response = call_gemini(client, JUDGE_SYSTEM, judge_prompt, model=model)
    scores = parse_judge_response(judge_response)

    overall = scores.get("overall_score", 0)
    emoji = "🟢" if overall >= 4 else "🟡" if overall >= 3 else "🔴"
    print(f"    {emoji} Score: {overall}/5 — {scores.get('explanation', '')[:80]}")

    # Rate limit pause
    time.sleep(2)

    return {
        "case_id": case_id,
        "category": case["category"],
        "verdict_expected": verdict,
        "status": "ok",
        "ai_response": ai_response,
        "scores": scores,
    }


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate AI Legal Assistant")
    parser.add_argument("--limit", type=int, help="Max cases to evaluate")
    parser.add_argument("--only", choices=["criminal", "civil", "administrative", "constitutional"])
    parser.add_argument("--resume-from", type=str, help="Resume from case_id")
    parser.add_argument("--model", type=str, default="gemini-3.1-pro-preview", help="Gemini model")
    args = parser.parse_args()

    print("=" * 60)
    print("🏛️  AI Legal Assistant Evaluation")
    print("=" * 60)
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Model: {args.model}")

    # Load cases
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = data["cases"]
    print(f"Loaded: {len(cases)} cases from {CASES_FILE.name}")

    # Filter
    if args.only:
        cases = [c for c in cases if c["category"] == args.only]
        print(f"Filtered to {args.only}: {len(cases)} cases")

    # Resume
    if args.resume_from:
        skip = True
        filtered = []
        for c in cases:
            if c["case_id"] == args.resume_from:
                skip = False
            if not skip:
                filtered.append(c)
        cases = filtered
        print(f"Resuming from {args.resume_from}: {len(cases)} cases remaining")

    # Limit
    if args.limit:
        cases = cases[:args.limit]
        print(f"Limited to {args.limit} cases")

    # Init Gemini
    print(f"\n🔌 Connecting to Gemini...")
    client = get_gemini_client()

    # Load existing results for resume
    existing_results = []
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            existing_results = existing_data.get("results", [])
            done_ids = {r["case_id"] for r in existing_results if r.get("status") == "ok"}
            cases = [c for c in cases if c["case_id"] not in done_ids]
            print(f"📂 Found {len(existing_results)} existing results, {len(cases)} remaining")

    # Run evaluation
    print(f"\n{'='*60}")
    print(f"🚀 Evaluating {len(cases)} cases...")
    print(f"{'='*60}")

    results = list(existing_results)
    for i, case in enumerate(cases, 1):
        result = evaluate_case(client, case, i, len(cases), model=args.model)
        results.append(result)

        # Save after each case (crash-safe)
        save_results(results, args.model)

    # Final report
    print_report(results)


def save_results(results: list, model: str):
    """Save results to disk (crash-safe)."""
    ok_results = [r for r in results if r.get("status") == "ok"]
    output = {
        "evaluated_at": datetime.now().isoformat(),
        "model": model,
        "total_evaluated": len(ok_results),
        "total_errors": len(results) - len(ok_results),
        "results": results,
    }

    # Calculate aggregate scores
    if ok_results:
        for metric in ["verdict_alignment", "legal_reasoning",
                        "article_accuracy", "practical_value", "overall_score"]:
            vals = [r["scores"].get(metric, 0) for r in ok_results if r.get("scores")]
            output[f"avg_{metric}"] = round(sum(vals) / len(vals), 2) if vals else 0

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def print_report(results: list):
    """Print final evaluation report."""
    ok = [r for r in results if r.get("status") == "ok"]

    print(f"\n{'='*60}")
    print(f"📊 EVALUATION REPORT")
    print(f"{'='*60}")
    print(f"  Total evaluated: {len(ok)}")
    print(f"  Errors: {len(results) - len(ok)}")

    if not ok:
        return

    # Aggregate scores
    print(f"\n  📈 Average Scores (1-5):")
    for metric in ["verdict_alignment", "legal_reasoning",
                    "article_accuracy", "practical_value", "overall_score"]:
        vals = [r["scores"].get(metric, 0) for r in ok if r.get("scores")]
        avg = sum(vals) / len(vals) if vals else 0
        bar = "█" * int(avg) + "░" * (5 - int(avg))
        print(f"    {metric:25s}: {avg:.2f} {bar}")

    # By category
    print(f"\n  📁 By category:")
    cats = {}
    for r in ok:
        cat = r.get("category", "?")
        if cat not in cats:
            cats[cat] = []
        cats[cat].append(r["scores"].get("overall_score", 0))
    for cat, scores in sorted(cats.items()):
        avg = sum(scores) / len(scores)
        print(f"    {cat:20s}: {avg:.2f} ({len(scores)} cases)")

    # Score distribution
    print(f"\n  📊 Score distribution:")
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in ok:
        s = r["scores"].get("overall_score", 0)
        if s in dist:
            dist[s] += 1
    for score, count in sorted(dist.items()):
        bar = "█" * count
        print(f"    {score}/5: {bar} ({count})")

    print(f"\n  💾 Results saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
