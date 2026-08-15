# Open Design — Business Brief for ბუნდოვანი კანონი

## What to do once open-design is running

### 1. Add our custom design system

Copy `DESIGN.md` (the one created below) into:
```
open-design/design-systems/fuzzzy-law/DESIGN.md
```

Then select **"ბუნდოვანი კანონი"** from the Design System dropdown in the UI.

### 2. Use the `mobile-app` skill

Select the **mobile-app** skill from the skill picker and enter the prompts below
to generate each screen. Generate them one at a time.

### 3. Screen generation prompts

#### Prompt 1 — Chat Screen (Main)
```
Design the main chat screen for "ბუნდოვანი კანონი" (Fuzzzy Law), a Georgian AI legal assistant app. 
The screen shows a conversation between a user and an AI legal advisor. 
- User messages are right-aligned bubbles
- AI responses are left-aligned with a thin accent left border, containing structured legal advice with tappable citation chips like "§ მუხ. 316 სამოქ. კოდ."
- AI thinking indicator: 3 pulsing dots with text "ბუნდოვანი კანონი ფიქრობს..."
- Bottom: pill-shaped chat input with send button, placeholder "აღწერეთ თქვენი სიტუაცია..."
- Bottom navigation bar: Chat (active), Laws, Notes, Profile
- The tone is premium, trustworthy, and Georgian-rooted
```

#### Prompt 2 — Law Browser
```
Design the law browser screen for a Georgian legal assistant app.
- App bar: "კანონები" (Laws) with search icon
- Search bar below for full-text search
- 2-column category grid with colored accent dots:
  Criminal (red), Civil (blue), Administrative (green), Labor (orange), Tax (purple), Family (pink), Property (teal)
- Below: scrollable list of law code cards, each with a 4px colored left accent bar, title in Georgian, subtitle with article count, chevron right
- Bottom navigation: Chat, Laws (active), Notes, Profile
- Premium legal feel, readable Georgian typography
```

#### Prompt 3 — Conversation List / Home
```
Design the home/conversation list screen for a Georgian AI legal assistant.
- App bar: app logo + "ბუნდოვანი კანონი" title
- Search bar
- List of past AI consultations, each showing:
  - Auto-generated title from first message
  - 1-line preview of last message
  - Date + legal domain badge (colored chip)
- FAB: "+" button to start new consultation
- Empty state for new users: illustration + "დაიწყეთ პირველი კონსულტაცია" (Start your first consultation)
- Bottom navigation: Chat (active), Laws, Notes, Profile
```

#### Prompt 4 — Notes Screen
```
Design the notes screen for a Georgian legal assistant app.
- App bar: "ჩანაწერები" (Notes) with search icon
- Horizontal scrollable filter chips: All, AI Responses, Law Articles, Personal Notes
- List of note cards, each showing:
  - Note title
  - 3-line content preview (truncated)
  - Source badge: "AI პასუხი" | "კანონის მუხლი" | "პირადი ჩანაწერი"
  - Date + legal domain tag chips
- Swipe-to-delete hint
- FAB: "+" to create new personal note
- Empty state: "შეინახეთ პირველი ჩანაწერი" (Save your first note)
- Bottom navigation: Chat, Laws, Notes (active), Profile
```

#### Prompt 5 — Onboarding (Page 1)
```
Design the first onboarding page for a Georgian AI legal assistant.
- Dark, premium background
- Centered illustration: person talking to AI with speech bubbles
- Headline: "დასვით ნებისმიერი იურიდიული კითხვა" (Ask Any Legal Question)
- Body text: "აღწერეთ თქვენი სიტუაცია ჩვეულებრივი სიტყვებით — ჩვენ ვიპოვით საჭირო კანონებს"
- Bottom: dot page indicators (1 of 3) + "გამოტოვება" (Skip) text + "შემდეგი" (Next) button
- Premium, inspiring, trustworthy mood
```

#### Prompt 6 — Analysis Results
```
Design the AI analysis results screen for a Georgian legal assistant.
- Shows structured legal analysis with collapsible sections:
  📋 სიტუაციის შეჯამება (Situation Summary)
  ⚖️ გამოსაყენებელი კანონები (Applicable Laws)
  🛡️ რეკომენდებული სტრატეგია (Recommended Strategy)
  📊 ალტერნატივები (Alternatives)
  ⚠️ რისკები (Risks)
  📅 შემდეგი ნაბიჯები (Next Steps)
- Each section: card with left accent bar, expand/collapse
- Citation chips throughout that are tappable
- Copy and Save to Notes buttons per section
- Scrollable, with app bar showing conversation title
```

### 4. Export & Capture

After generating each screen:
1. **Export as HTML** from the open-design UI
2. **Screenshot** each mockup
3. Save exports to `master_plan/design/mockups/`

### 5. Extract Design Tokens → Flutter

Once you're happy with the generated designs, I will:
1. Extract the exact color palette, typography, spacing the AI chose
2. Map them into `frontend/packages/ui_kit/` (UiKitColors, UiTextStyles, UiFormStyles, UiColors theme extension)
3. Update the Flutter theme to match

---

## The design system file to create

See: `open-design/design-systems/fuzzzy-law/DESIGN.md` (create this manually or I'll create it once the repo is cloned)
