# 🏛️ Agent Prompt: Assess AI Legal Response Quality

> **Purpose:** Paste this into an Antigravity chat AFTER the evaluation pipeline has run
> and `merge_results.py` has produced the comparison files. The agent will read each
> case's AI response and score it against measurable criteria.

---

## PROMPT TO COPY-PASTE BELOW THIS LINE:

---

I need you to perform a thorough quality assessment of our AI legal assistant ("ბუნდოვანი კანონი — Fuzzzy Law"). We ran 30 real Georgian law cases through our RAG pipeline, and now I need you to compare the AI's responses against the actual court outcomes.

## 📁 FILES TO READ

1. **Full comparison data:**
   ```
   /Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/comparison/full_comparison.json
   ```

2. **Individual case comparisons (for deep analysis):**
   ```
   /Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/comparison/case_XXX_comparison.json
   ```

3. **Expected outcomes (ground truth):**
   ```
   /Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/results/case_XXX/expected_outcome.json
   ```

4. **AI responses (what the system generated):**
   ```
   /Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/results/case_XXX/ai_response.json
   ```

## 📊 SCORING CRITERIA (Score each case 1-5 on each criterion)

### 1. Legal Accuracy (weight: 30%)
- **5:** Correctly identifies ALL relevant laws, correct interpretation, matches actual court reasoning
- **4:** Identifies most relevant laws (>80%), minor interpretation differences
- **3:** Identifies some relevant laws (50-80%), some misinterpretations
- **2:** Misses major applicable laws, significant errors in interpretation
- **1:** Fundamentally wrong legal analysis, hallucinated laws, dangerous advice

### 2. Article Citation Recall (weight: 20%)
- **5:** ALL expected law articles are cited and correctly referenced
- **4:** Most expected articles cited (>80%)
- **3:** About half of expected articles cited (50-80%)
- **2:** Few expected articles cited (<50%)
- **1:** Almost no expected articles found, or mostly hallucinated citations

### 3. Outcome Prediction (weight: 20%)
- **5:** AI's assessment matches the actual court outcome (verdict, sentence range, reasoning)
- **4:** AI suggests the actual outcome as the most likely scenario
- **3:** AI mentions the actual outcome but doesn't prioritize it
- **2:** AI gives a different primary prediction but acknowledges the possibility
- **1:** AI's prediction is completely different from actual outcome

### 4. Practical Usefulness (weight: 15%)
- **5:** Advice is immediately actionable, includes specific steps, deadlines, realistic costs
- **4:** Mostly actionable, some gaps in practical guidance
- **3:** Partially useful, too theoretical or vague on next steps
- **2:** Limited practical value, mostly academic legal analysis
- **1:** Useless for a real person facing this situation

### 5. Completeness & Balance (weight: 15%)
- **5:** Covers defense strategies, prosecution arguments, risks, alternatives — comprehensive
- **4:** Good coverage, minor gaps in one area
- **3:** Covers basics but misses important angles (e.g., no counter-arguments)
- **2:** Incomplete — misses major defense strategies or risks
- **1:** Severely incomplete or one-sided

## 📋 OUTPUT FORMAT

### Per-Case Assessment
For each of the 30 cases, produce:

```json
{
  "case_id": "CASE_001",
  "scores": {
    "legal_accuracy": 4,
    "article_recall": 3,
    "outcome_prediction": 4,
    "practical_usefulness": 5,
    "completeness": 4
  },
  "weighted_score": 3.95,
  "grade": "B+",
  "strengths": [
    "Correctly identified primary criminal charge",
    "Good practical advice with specific deadlines"
  ],
  "weaknesses": [
    "Missed administrative offences code applicability",
    "Did not discuss plea bargain option"
  ],
  "hallucinations": [
    "Referenced მუხლი 245 which doesn't exist in current code"
  ],
  "dangerous_advice": [],
  "notes": "Overall good response but missed some procedural rights"
}
```

### Aggregate Report
After scoring all cases, produce a summary:

```json
{
  "overall_weighted_score": 3.85,
  "overall_grade": "B+",
  "total_cases_assessed": 30,
  "grade_distribution": {"A": 5, "B+": 8, "B": 7, "C+": 5, "C": 3, "D": 2, "F": 0},
  "avg_scores_by_criterion": {
    "legal_accuracy": 3.8,
    "article_recall": 3.2,
    "outcome_prediction": 3.5,
    "practical_usefulness": 4.1,
    "completeness": 3.6
  },
  "avg_scores_by_category": {
    "criminal": 3.9,
    "civil": 3.7,
    "labor": 3.5,
    "administrative": 3.3,
    "other": 3.2
  },
  "avg_scores_by_difficulty": {
    "easy": 4.2,
    "medium": 3.7,
    "hard": 3.1
  },
  "top_3_strengths": [
    "Consistently good practical advice",
    "Strong criminal law coverage",
    "Honest disclaimers about uncertainty"
  ],
  "top_3_weaknesses": [
    "Weak on administrative procedure",
    "Sometimes hallucinated article numbers",
    "Missed procedural deadlines in 40% of cases"
  ],
  "critical_failures": [
    {"case_id": "CASE_015", "issue": "Recommended action that would violate statute of limitations"}
  ],
  "recommendations": [
    "Improve RAG retrieval for administrative and labor code",
    "Add citation verification step to prevent hallucinated articles",
    "Include statute of limitations check in every criminal case"
  ]
}
```

### Grade Scale
- **A** (4.5-5.0): Excellent — Could serve as primary legal guidance
- **B+** (4.0-4.4): Very Good — Reliable with minor gaps
- **B** (3.5-3.9): Good — Useful but needs lawyer verification
- **C+** (3.0-3.4): Acceptable — General direction correct, significant gaps
- **C** (2.5-2.9): Below Average — Too many errors for practical use
- **D** (2.0-2.4): Poor — Unreliable, potentially harmful
- **F** (<2.0): Failing — Dangerous misinformation

## ⚠️ SPECIAL ATTENTION

1. **Hallucination Detection:** Flag ANY article number that doesn't exist in the actual Georgian legal codes (Criminal Code, Civil Code, Criminal Procedure, Civil Procedure, Administrative, Labor, Tax, Administrative Offences, General Administrative, Constitution, Juvenile Justice)
2. **Dangerous Advice:** Flag any advice that could result in the user losing rights, missing deadlines, or facing additional legal consequences
3. **Georgian Language Quality:** Note if the Georgian text is grammatically correct and natural-sounding
4. **Citation Verification:** Cross-check key article numbers the AI cites — are they real and relevant?

## 📁 SAVE OUTPUT TO

```
/Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/assessment/quality_report.json
/Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/assessment/quality_report.md
```

Read ALL 30 case comparisons, score each one carefully, then produce both the per-case scores and the aggregate report.
