# 💡 Ideas & Simplifiers — One-Touch Full Fillout

> Good ideas, UX simplifiers, and advanced features to make this the best legal case builder.

---

## 🎯 Core Simplifiers

### 1. "Tell me like you're telling a friend" Mode
Instead of structured questions, offer ONE big text box:
```
"აუხსენით სიტუაცია ისე, როგორც მეგობარს აუხსნიდით"
(Explain the situation like you'd explain to a friend)
```
AI extracts everything: dates, parties, evidence, desired outcome.
Falls back to specific questions only for gaps.

**Why this is better:** Most people can't decompose their problem into facts/dates/parties. But they CAN tell a story.

### 2. Suggested Situations (Quick Start Templates)
For common cases, offer pre-built templates:
```
📋 ხშირი საქმეები:
├── 🏠 ბინის ქირავნობის დავა
├── 💼 სამსახურიდან უკანონო გათავისუფლება
├── 🚗 ავტო ავარიის კომპენსაცია
├── 💰 ვალის დაბრუნება
├── 👨‍👩‍👧 ალიმენტი
└── 📝 ხელშეკრულების დარღვევა
```
Selecting a template pre-fills some wizard answers and asks only the specific details.

### 3. Example Answers on Every Step
Show real examples (blurred/anonymized) that users can tap to see format:
```
💡 მაგალითი:
"2025 წლის მარტში სამსახურიდან გამათავისუფლეს 
 წინასწარი გაფრთხილების გარეშე. 3 წელი ვმუშაობდი
 შპს „მაგალითში" ბუღალტრის პოზიციაზე."
```

---

## 🚀 Advanced Features

### 4. AI Follow-up Questions (Adaptive Wizard)
After the initial "tell your story" step, AI identifies gaps and asks ONLY what's missing:
```
AI: "თქვენ ახსენეთ ხელშეკრულება — 
     წერილობითი იყო თუ ზეპირი?"

AI: "მემამულემ ახსნა რატომ არ 
     აბრუნებს გირაოს?"

AI: "გაქვთ გადახდის ქვითარი 
     ან ბანკის ამონაწერი?"
```
Maximum 3 follow-up questions. AI marks confidence level for each section.

### 5. Smart Domain Auto-Detection
When user types their story, AI auto-detects legal domain:
```
User types: "სამსახურიდან გამათავისუფლეს..."
→ AI auto-selects: 🔶 შრომის სამართალი (Labor)
→ RAG queries pre-filtered to labor code
```
User can override, but 90% won't need to.

### 6. "What if?" Scenario Generator
After case generation, offer:
```
🔮 "რა მოხდება თუ...?"
├── "...მოწმე ვერ მოვიყვან?" → Strategy adjusts
├── "...ხელშეკრულება ვერ ვიპოვე?" → Evidence section updates
└── "...მეორე მხარე მედიაციას შემოგვთავაზებს?" → New strategy branch
```

### 7. Confidence Heatmap
Color-code each generated section by AI confidence:
```
📋 ფაქტები ██████████ 95% — ✅ საკმარისი ინფორმაცია
⚖️ არგუმენტები ████████░░ 80% — ✅ ძლიერი საფუძველი
🛡️ სტრატეგია ██████░░░░ 60% — ⚠️ საჭიროებს დაზუსტებას
⚠️ რისკები ████░░░░░░ 40% — ℹ️ მეტი ინფორმაცია სჭირდება
```
Low-confidence sections get a "💬 დასვით AI-ს კითხვა" button.

### 8. Case Comparison
"Similar cases" section at the bottom:
```
📊 მსგავსი საქმეები:
├── ბინის გირაოს დავა (2024) — მოგებული ✅
├── ქირავნობის ხელშეკრულება (2023) — მოგებული ✅
└── გირაოს დაბრუნება (2024) — ნაწილობრივ 🟡
```
(This requires case law data — future feature, but design the UI slot now)

---

## 🛡️ Trust & Safety

### 9. Honest Disclaimer Flow
Before generation, show:
```
⚠️ მნიშვნელოვანი:

AI-ის ანალიზი არ არის იურიდიული რჩევა.
ყოველი მოხმობილი კანონის მუხლი 
შეგიძლიათ შეამოწმოთ matsne.gov.ge-ზე.

რთულ საქმეებზე გირჩევთ ადვოკატს.
[📞 უფასო იურიდიული დახმარება: 2 92 12 92]

[✅ გავიგე, გაგრძელება]
```

### 10. "Red Team" Auto-Check
After generation, automatically run a second AI pass:
```
🤔 "რას იტყვის მეორე მხარე?"
```
This populates the Risks tab with counter-arguments and pre-builds your responses.

---

## ⚡ Performance Optimizations

### 11. Skeleton Loading with Section Labels
While generating, show the case structure with pulsing skeletons:
```
📋 ფაქტები ████░░░░░░░░ ანალიზი...
⚖️ არგუმენტები ░░░░░░░░░░ მოლოდინში...
🛡️ სტრატეგია ░░░░░░░░░░ მოლოდინში...
```
Sections fill in as they're generated (if using multi-step).

### 12. Offline Intake + Online Generation
Wizard works fully offline (saves to Hive).
Generation requires network but user can start the wizard anytime.
```
✈️ ოფლაინ: კითხვებზე პასუხის გაცემა
🌐 ონლაინ: AI გენერაცია
```

---

## 📐 Architecture Simplifiers

### 13. Reuse Existing CaseData Model
Don't create a separate "generated case" model. Map AI output directly to existing CaseData fields:
- `facts` → `List<FactData>`
- `arguments` → `List<ArgumentData>`
- etc.

This means the generated case is immediately editable in the existing workspace.

### 14. Single Cubit for Wizard
```dart
class CaseWizardCubit extends Cubit<CaseWizardState> {
  // Wizard steps
  void updateSituation(String text);
  void updateDate(DateTime? date, DatePrecision precision);
  void updateOpponent(OpponentType type, String description);
  void updateEvidence(List<EvidenceType> existing);
  void updateDesiredOutcome(OutcomeType outcome);
  void submitForGeneration();
  
  // Progress tracking
  void onSectionGenerated(String section, dynamic data);
}
```

### 15. Backend: Extend Existing CaseBuilderService
Don't create a new service. Add `build_from_intake()` method to `CaseBuilderService`:
```python
async def build_from_intake(
    self, db, user_id, case_id, intake: IntakeData
) -> dict[str, Any]:
    # 1. AI extracts legal issues from intake
    # 2. Multiple RAG queries per issue
    # 3. Generate sections (possibly in parallel)
    # 4. Verify citations
    # 5. Return structured case
```

---

## Priority Matrix

| Idea | Impact | Effort | Priority |
|------|--------|--------|----------|
| Tell-a-friend mode (#1) | 🔴 High | Medium | P0 — Must have |
| Quick Start Templates (#2) | 🟡 Medium | Low | P1 — Should have |
| Example answers (#3) | 🟡 Medium | Low | P1 — Should have |
| Adaptive follow-ups (#4) | 🔴 High | High | P0 — Must have |
| Domain auto-detect (#5) | 🟡 Medium | Low | P1 — Should have |
| "What if?" scenarios (#6) | 🟡 Medium | High | P2 — Nice to have |
| Confidence heatmap (#7) | 🟢 Low | Low | P1 — Should have |
| Case comparison (#8) | 🟢 Low | High | P3 — Future |
| Honest disclaimer (#9) | 🔴 High | Low | P0 — Must have |
| Red Team auto-check (#10) | 🔴 High | Medium | P0 — Must have |
| Skeleton loading (#11) | 🟡 Medium | Low | P1 — Should have |
| Offline intake (#12) | 🟡 Medium | Low | P1 — Should have |
