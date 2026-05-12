# 📊 Eval Analysis — 17 Cases (3 Civil + 14 Criminal)

## Overall Scores

| Metric | Average | Rating |
|--------|---------|--------|
| **Overall Score** | **3.47/5** | 🟡 Good but needs improvement |
| Article Accuracy | 4.29/5 | 🟢 Strong |
| Practical Value | 3.47/5 | 🟡 Moderate |
| Legal Reasoning | 3.41/5 | 🟡 Moderate |
| Verdict Alignment | 3.00/5 | 🔴 Weakest metric |

## Score Distribution

| Score | Count | Cases |
|-------|-------|-------|
| ⭐⭐⭐⭐⭐ 5/5 | 8 | CIVI-1008, CIVI-1042, CRIM-1039, CRIM-1214, CRIM-1224, CRIM-1296, CRIM-172, CRIM-18I |
| ⭐⭐⭐⭐ 4/5 | 1 | CRIM-152 |
| ⭐⭐⭐ 3/5 | 2 | CIVI-1112, CRIM-122 |
| ⭐⭐ 2/5 | 3 | CRIM-1051, CRIM-1086, CRIM-1331 |
| ⭐ 1/5 | 3 | CRIM-1340, CRIM-201, CRIM-311 |

> [!IMPORTANT]
> 47% of cases scored 5/5 (perfect). But **35% scored ≤2/5** — these are dangerous failures where the AI gave wrong legal advice.

---

## 🔴 Critical Finding: Verdict Prediction Bias

The AI has a **strong bias toward predicting that appeals will be rejected**.

| Actual Verdict | Avg Score | Cases | Problem |
|----------------|-----------|-------|---------|
| Appeal rejected (არ დაკმაყოფილდა) | **4.2-5.0** | 6 | ✅ AI predicts these well |
| Appeal granted (დაკმაყოფილდა) | **2.2** | 4 | 🔴 AI almost always gets these wrong |
| Partially granted (ნაწილობრივ) | **3.4** | 5 | 🟡 Mixed results |
| Verdict modified (ცვლილება) | **3.5** | 2 | 🟡 Mixed results |

**Root cause:** The AI defaults to "the lower court was right" reasoning. It mirrors standard legal conservatism, but the Supreme Court overturns more often than the AI expects.

---

## 🔍 Failure Patterns (6 low-scoring cases)

### Pattern 1: Missing Procedural/Evidence Context (2 cases)

| Case | Score | What happened |
|------|-------|---------------|
| CRIM-1340 | 1/5 | AI focused on material law (qualification), but court acquitted based on **evidence failure** (victim changed testimony) |
| CRIM-1086 | 2/5 | AI predicted acquittal on threats (151), court convicted. AI predicted downgrade (353→353¹), court did opposite |

> **The AI analyzes the law correctly but ignores that courts often decide based on evidence admissibility and witness credibility, not just legal theory.**

### Pattern 2: Unknown Supreme Court Precedents (2 cases)

| Case | Score | What happened |
|------|-------|---------------|
| CRIM-1051 | 2/5 | AI said formal disability status required for aggravation. Supreme Court ruled **factual** disability is sufficient |
| CRIM-1331 | 2/5 | AI said putting drugs at a location = attempted sale. Supreme Court ruled it's only **preparation** (not attempt) without buyer communication proof |

> **The AI doesn't know specific Georgian Supreme Court precedent interpretations that differ from textbook law.**

### Pattern 3: Missing Mandatory Sentencing Rules (2 cases)

| Case | Score | What happened |
|------|-------|---------------|
| CRIM-201 | 1/5 | AI missed that სსკ 44§4 prohibits community service for pensioners. Court had to impose imprisonment instead |
| CRIM-311 | 1/5 | AI missed სსკ 53¹ mandatory +1 year for weapon use. Court applied this imperative rule |

> **The AI knows the main articles but misses specific mandatory sentencing provisions that change the outcome.**

---

## 💡 Proposed Improvements

### 1. Enhance System Prompt — Add Procedural Awareness
```
Current: "განსაზღვროთ რომელი კანონის რომელი მუხლები გამოიყენება"
```
```
Add: "ყურადღება მიაქციეთ საპროცესო ასპექტებს:
- მტკიცებულებების დასაშვებობა და სარწმუნოობა
- მოწმის/დაზარალებულის ჩვენების შეცვლის შესაძლებლობა  
- გონივრულ ეჭვს მიღმა სტანდარტი
- საკასაციო სასამართლოს შეზღუდული კომპეტენცია ფაქტების დადგენაში"
```

### 2. Add Mandatory Sentencing Checklist to Prompt
```
Add: "სასჯელის განსაზღვრისას აუცილებლად შეამოწმეთ:
- სსკ 53¹ — იარაღით ჩადენილი დანაშაულისთვის სავალდებულო დამძიმება
- სსკ 44§4 — საპენსიო ასაკის პირს შრომა არ ენიშნება  
- სსკ 50§5 — პირობითი ჩათვლის შეზღუდვები
- ამნისტიის კანონი — მოქმედი ამნისტიის ეფექტი სასჯელზე"
```

### 3. Two-Pass Verdict Prediction
Instead of one prediction, ask AI to consider **both outcomes**:
```
"განიხილეთ ორი სცენარი:
ა) რატომ შეიძლება საჩივარი დაკმაყოფილდეს
ბ) რატომ შეიძლება არ დაკმაყოფილდეს
შემდეგ აირჩიეთ უფრო სავარაუდო"
```

### 4. RAG Integration (Future)
Feed the AI our **law corpus (9,450 chunks)** alongside the case facts. This would:
- Give it access to exact article text (not just from training data)
- Include recent amendments and mandatory provisions
- Reduce article citation errors

### 5. Add Supreme Court Practice Examples
Include 3-5 example Supreme Court reasoning patterns in the system prompt:
- "When the Supreme Court overturns" patterns
- Evidence-based acquittal patterns
- Mandatory sentencing rule application patterns

---

## 📋 Next Steps

1. **Run remaining 33 cases** (civil, admin, constitutional) to get full picture
2. **Implement improvements #1-#3** in the system prompt (quick wins, no code change needed)  
3. **Re-run the 6 failed cases** with improved prompt to measure delta
4. **Plan RAG integration** (#4) for production accuracy boost
