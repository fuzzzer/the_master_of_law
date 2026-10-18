# 🏛️ Agent Prompt: Gather 50(Or More as Possible reliably) Real Georgian Law Cases with Verified Outcomes

> **Purpose:** Paste this entire prompt into a NEW Antigravity conversation.
> The agent will search the web for real Georgian court cases from official sources,
> and produce a structured JSON dataset you can use to evaluate Fuzzzy Law RAG pipeline.

---

## PROMPT TO COPY-PASTE BELOW THIS LINE:

---

I need you to research and gather **50(Or More as Possible reliably) real Georgian (country, საქართველო) law cases** with **verified court outcomes**. These will be used to evaluate an AI legal assistant.

## ⚠️ CRITICAL REQUIREMENTS

1. **ONLY Georgia the country (საქართველო)** — NOT the US state of Georgia
2. **Cases MUST have real, verified outcomes** (court verdict, sentence, ruling)
3. **Cases must be based on currently valid Georgian law** (consolidated/კონსოლიდირებული versions)
4. **Diversity across legal domains** — I need cases from ALL these areas:
   - Criminal Code (სისხლის სამართლის კოდექსი) — at least 8 cases
   - Civil Code (სამოქალაქო კოდექსი) — at least 6 cases
   - Labor Code (შრომის კოდექსი) — at least 4 cases
   - Administrative Code / Administrative Offences — at least 4 cases
   - Criminal Procedure (საპროცესო) — at least 3 cases
   - Other (Constitutional, Tax, Juvenile Justice) — at least 5 cases

## 📋 SEARCH SOURCES (in priority order)

Search these **official Georgian sources** for real cases:

1. **საქართველოს უზენაესი სასამართლო (Supreme Court)**
   - URL: `https://www.supremecourt.ge/ka/cases`
   - გადაწყვეტილებები section — search for criminal, civil, administrative decisions
   - Also check: `https://www.supremecourt.ge/ka/decisions` (periodic publications of decisions)
   - Also check: `https://www.supremecourt.ge/ka/analytics` (analytics/case law summaries)

2. **court.ge (საერთო სასამართლოების პორტალი)**
   - URL: `https://court.ge`
   - General courts portal with case search

3. **საკონსტიტუციო სასამართლო (Constitutional Court)**
   - URL: `https://www.constcourt.ge`
   - For constitutional review cases

4. **Courtwatch.ge (სასამართლოს გუშაგი)**
   - URL: `https://courtwatch.ge`
   - Independent court monitoring — has detailed case analyses with outcomes

5. **GYLA (საქართველოს ახალგაზრდა იურისტთა ასოციაცია)**
   - URL: `https://gyla.ge`
   - Strategic litigation cases with results in "შედეგები" section

6. **HCOJ (იუსტიციის უმაღლესი საბჭო)**
   - URL: `https://hcoj.gov.ge`

7. **Georgian legal news sites** for reported case outcomes:
   - `https://www.radiotavisupleba.ge` (RFE/RL Georgian)
   - `https://www.interpressnews.ge`
   - `https://www.civil.ge` (Civil Georgia)
   - `https://bm.ge`
   - `https://www.primetime.ge`

8. **matsne.gov.ge** — for verifying that referenced law articles are current/consolidated

## 📊 OUTPUT FORMAT

For EACH case, provide this exact JSON structure. Output ALL cases in a single JSON array.

```json
[
  {
    "case_id": "CASE_001",
    "category": "criminal",
    "subcategory": "assault",
    "title_ka": "მეზობლის ცემის საქმე",
    "title_en": "Neighbor Assault Case",
    "source_url": "https://supremecourt.ge/ka/cases/...",
    "source_name": "Supreme Court of Georgia",
    "year": 2024,
    "court_instance": "Supreme Court / Cassation",
    
    "situation_description_ka": "2023 წლის მარტში, ბრალდებულმა ფიზიკური შეურაცხყოფა მიაყენა მეზობელს საცხოვრებელ ბინაში. დაზარალებულმა მიიღო მსუბუქი ხარისხის ჯანმრთელობის დაზიანება...",
    "situation_description_en": "In March 2023, the defendant physically assaulted their neighbor in a residential apartment. The victim sustained minor health damage...",
    
    "user_question_ka": "მეზობელმა დამარტყა და ჯანმრთელობა დამიზიანა. რა სასჯელი ემუქრება მას და რა უფლებები მაქვს?",
    "user_question_en": "My neighbor hit me and damaged my health. What punishment does he face and what are my rights?",
    
    "applicable_laws": [
      {
        "code": "სისხლის სამართლის კოდექსი",
        "article": "მუხლი 120",
        "title": "ჯანმრთელობის განზრახ მსუბუქი დაზიანება",
        "relevance": "Primary charge"
      },
      {
        "code": "სისხლის სამართლის საპროცესო კოდექსი",
        "article": "მუხლი 57",
        "title": "დაზარალებულის უფლებები",
        "relevance": "Victim's procedural rights"
      }
    ],
    
    "actual_outcome": {
      "verdict": "guilty",
      "sentence": "ჯარიმა 2000 ლარი, პირობითი მსჯავრი 1 წელი",
      "sentence_en": "Fine of 2000 GEL, 1 year probation",
      "key_reasoning": "Court found that the assault was proven by medical evidence and witness testimony. Mitigating circumstances (first offense, reconciliation attempt) led to a lighter sentence.",
      "key_articles_applied": ["SSK მუხლი 120", "SSK მუხლი 53"]
    },
    
    "difficulty": "medium",
    "tags": ["criminal", "assault", "minor_injury", "neighbor_dispute"],
    "verification_notes": "Verified from Supreme Court decision database, case published in 2024 analytics report."
  }
]
```

## 🎯 CASE DIVERSITY REQUIREMENTS

Make sure cases cover these specific scenarios (at minimum):

### Criminal (8+ cases):
1. Assault / bodily harm (ცემა, ჯანმრთელობის დაზიანება)
2. Theft / robbery (ქურდობა, ძარცვა)
3. Self-defense claim (აუცილებელი მოგერიება)
4. Drug-related offense (ნარკოტიკული დანაშაული)
5. Domestic violence (ოჯახური ძალადობა)
6. Fraud (თაღლითობა)
7. DUI / traffic criminal offense (მაღალი სიჩქარით ან ნასვამ მდგომარეობაში)
8. Murder / manslaughter with mitigating circumstances

### Civil (6+ cases):
9. Property inheritance dispute (მემკვიდრეობის დავა)
10. Contract breach (ხელშეკრულების დარღვევა)
11. Divorce / alimony (განქორწინება, ალიმენტი)
12. Property damage (ქონების დაზიანება)
13. Landlord-tenant dispute (ქირავნობის დავა)
14. Debt collection / loan default (სესხის დავა)

### Labor (4+ cases):
15. Wrongful termination (უკანონო გათავისუფლება)
16. Unpaid wages (ხელფასის გაუცემლობა)
17. Workplace discrimination (დისკრიმინაცია სამუშაო ადგილზე)
18. Workplace injury (სამუშაო ადგილზე ტრავმა)

### Administrative (4+ cases):
19. Traffic fine challenge (საგზაო ჯარიმის გასაჩივრება)
20. Building permit dispute (მშენებლობის ნებართვა)
21. Tax dispute (საგადასახადო დავა)
22. Government decision challenge (ადმინისტრაციული აქტის გასაჩივრება)

### Other (5+ cases):
23. Constitutional rights case (საკონსტიტუციო უფლებები)
24. Juvenile justice case (არასრულწლოვანთა მართლმსაჯულება)
25. Data protection / privacy (პერსონალური მონაცემები)
26. Consumer protection
27. Environmental law violation
28. Media / defamation case
29-30. Any additional interesting cases

## 🔍 SEARCH STRATEGY

For each case you find:

1. **Search web** for the case on the official sources listed above
2. **Verify** the laws referenced are still current by cross-checking with matsne.gov.ge
3. **Confirm** the outcome is real (not hypothetical) — cite the source
4. **Extract** the specific law articles that were applied
5. If you can't find a REAL case for a specific scenario, search Georgian news sites for reported court decisions
6. If a case outcome mentions specific article numbers, verify they exist in the current version of the code

## 📝 FINAL DELIVERABLE

Save the complete JSON array to this file:
```
/Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/test_cases/cases.json
```

Also create a summary markdown file at:
```
/Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/eval/test_cases/CASES_README.md
```

The README should contain:
- Table of all 50(Or More as Possible reliably) cases with: ID, category, title, source, year, difficulty
- Source credibility notes
- Any caveats about specific cases
- Count by category

## ⚠️ IMPORTANT WARNINGS

- **DO NOT** include cases from the US state of Georgia
- **DO NOT** fabricate case outcomes — if you can't verify, skip and find another
- **DO NOT** use outdated law articles — verify against current consolidated versions on matsne.gov.ge
- **PREFER** cases from 2020-2025 for maximum relevance
- **Georgian text quality matters** — user questions should sound like how a real Georgian person would describe their situation to a lawyer
- Cases should range in difficulty: 10 easy, 10 medium, 10 hard
