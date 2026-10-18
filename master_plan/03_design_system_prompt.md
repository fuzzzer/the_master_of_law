# 🎨 Prompt 03 — Flutter App Design System & UI Specification

> **Purpose:** Define the complete design system, screen specifications, and UX flows for the Flutter mobile application. This prompt is designed to be sent to a design AI (e.g., Stitch, v0, or Figma AI) to generate visual mockups, AND to a coding AI agent to implement the Flutter app.

---

## System Identity

You are **LegalDesignArchitect**, an expert mobile UI/UX designer specializing in legal technology applications. Design a premium, trustworthy, and accessible mobile experience for "ბუნდოვანი კანონი" (Fuzzzy Law) — a Georgian legal assistant that makes law understandable for everyone.

---

## Brand Identity

### Name & Tagline
- **App Name:** ბუნდოვანი კანონი (Fuzzzy Law)
- **English:** Fuzzzy Law
- **Tagline (KA):** შენი პირადი იურისტი — ყოველთვის ხელთ
- **Tagline (EN):** Your personal lawyer — always at hand

### Brand Personality
- **Trustworthy** — This is law; users must feel safe and confident
- **Intelligent** — Advanced AI, but never condescending
- **Approachable** — Non-lawyers should never feel intimidated
- **Georgian** — Proudly rooted in Georgian culture and language
- **Premium** — A product that feels like a luxury legal retainer

### Logo Concept
- Stylized scales of justice merged with Georgian Mkhedruli letterform "კ" (for კანონი/law)
- Clean, geometric, works at all sizes
- Primary version + monochrome + app icon variants

---

## Design Tokens

### Color Palette

```
// Primary — Deep Judicial Navy
primary-900:  #0A1628    // Darkest — app bars, headers
primary-800:  #111D35
primary-700:  #1A2845    // Primary dark
primary-600:  #243558
primary-500:  #2E436B    // Primary base
primary-400:  #4A6490
primary-300:  #7088AB
primary-200:  #9BAFC8
primary-100:  #C8D5E4
primary-50:   #EDF1F7    // Lightest — backgrounds

// Accent — Georgian Gold
accent-900:   #6B4D00
accent-800:   #8A6300
accent-700:   #A87A00
accent-600:   #C79200    // Accent dark
accent-500:   #E5AA00    // Accent base — CTAs, highlights
accent-400:   #F0C040
accent-300:   #F5D370
accent-200:   #FAE5A0
accent-100:   #FDF2CF
accent-50:    #FFFAEB    // Lightest

// Semantic Colors
success:      #16A34A    // Favorable outcome, valid citations
success-bg:   #F0FDF4
warning:      #D97706    // Caution, deadlines approaching
warning-bg:   #FFFBEB
error:        #DC2626    // Invalid, danger, criminal charges
error-bg:     #FEF2F2
info:         #2563EB    // Informational, neutral legal facts
info-bg:      #EFF6FF

// Neutrals
neutral-950:  #0A0A0A
neutral-900:  #171717
neutral-800:  #262626
neutral-700:  #404040
neutral-600:  #525252
neutral-500:  #737373
neutral-400:  #A3A3A3
neutral-300:  #D4D4D4
neutral-200:  #E5E5E5
neutral-100:  #F5F5F5
neutral-50:   #FAFAFA
white:        #FFFFFF

// Dark Mode Surfaces
dark-surface-0:  #0A1628   // Base background
dark-surface-1:  #111D35   // Card level 1
dark-surface-2:  #1A2845   // Card level 2
dark-surface-3:  #243558   // Elevated elements
dark-border:     #2E436B   // Borders in dark mode
```

### Typography

```
// Font Family: Google Fonts
primary-font:     "Inter"          // Latin text
georgian-font:    "Noto Sans Georgian"  // Georgian text
mono-font:        "JetBrains Mono" // Code, article numbers

// Scale (Mobile)
display-large:    32px / 40px / -0.5px / 700    // Hero text
display-medium:   28px / 36px / 0px / 700       // Screen titles
headline-large:   24px / 32px / 0px / 600       // Section headers
headline-medium:  20px / 28px / 0.15px / 600    // Card titles
title-large:      18px / 26px / 0px / 600       // Subsection titles
title-medium:     16px / 24px / 0.15px / 500    // List item titles
body-large:       16px / 24px / 0.5px / 400     // Primary body text
body-medium:      14px / 20px / 0.25px / 400    // Secondary body text
body-small:       12px / 16px / 0.4px / 400     // Captions, metadata
label-large:      14px / 20px / 0.1px / 500     // Buttons
label-medium:     12px / 16px / 0.5px / 500     // Chips, tags
label-small:      11px / 16px / 0.5px / 500     // Overlines
```

### Spacing & Layout

```
space-xs:    4px
space-sm:    8px
space-md:    12px
space-lg:    16px
space-xl:    20px
space-2xl:   24px
space-3xl:   32px
space-4xl:   40px
space-5xl:   48px
space-6xl:   64px

// Content width
max-content-width:  600px
padding-horizontal:  20px
padding-vertical:    16px

// Border radius
radius-sm:    8px
radius-md:    12px
radius-lg:    16px
radius-xl:    20px
radius-full:  9999px
```

### Elevation & Shadows

```
// Light mode
elevation-1:  0 1px 3px rgba(10, 22, 40, 0.08)
elevation-2:  0 4px 12px rgba(10, 22, 40, 0.10)
elevation-3:  0 8px 24px rgba(10, 22, 40, 0.12)
elevation-4:  0 16px 48px rgba(10, 22, 40, 0.16)

// Dark mode — use lighter, subtler shadows + border emphasis
dark-elevation-1:  0 1px 3px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.03)
```

### Motion & Animation

```
// Durations
duration-fast:     150ms
duration-normal:   250ms
duration-slow:     400ms
duration-enter:    300ms
duration-exit:     200ms

// Curves
curve-ease-out:    cubic-bezier(0.0, 0.0, 0.2, 1.0)   // Enter
curve-ease-in:     cubic-bezier(0.4, 0.0, 1.0, 1.0)   // Exit
curve-standard:    cubic-bezier(0.4, 0.0, 0.2, 1.0)   // Move
curve-spring:      cubic-bezier(0.34, 1.56, 0.64, 1)  // Bounce/delight

// Principles
// - Chat messages: slide up + fade in (150ms, ease-out)
// - Screen transitions: shared axis (300ms, standard)
// - Buttons: scale 0.97 on press (100ms, spring)
// - Loading states: shimmer effect on content placeholders
// - AI thinking: pulsing dot animation (3 dots, staggered)
```

---

## Component Library

### 1. Chat Components

#### ChatBubble
```
// User message (right-aligned)
- Background: accent-500
- Text: white
- Border radius: radius-lg (top-left, top-right, bottom-left) + radius-sm (bottom-right)
- Padding: space-md horizontal, space-sm vertical
- Max width: 80% of screen
- Timestamp: body-small, semi-transparent below bubble

// AI message (left-aligned)  
- Background: primary-50 (light) / dark-surface-2 (dark)
- Text: neutral-900 (light) / neutral-100 (dark)
- Border radius: radius-lg (top-left, top-right, bottom-right) + radius-sm (bottom-left)
- Left accent border: 3px accent-500
- Contains: formatted text, law citations (tappable), action buttons
- Copy button: top-right corner, appears on long-press or hover
- Save to Notes button: bookmark icon, top-right
```

#### ChatInput
```
- Container: rounded pill shape (radius-full), elevation-2
- Background: white (light) / dark-surface-2 (dark)
- Placeholder: "აღწერეთ თქვენი სიტუაცია..." (Describe your situation...)
- Send button: circular, accent-500, arrow-up icon
- Microphone button: for voice input (future)
- Attachment button: for document upload (future)
- Min height: 48px, expands to max 120px with multiline text
```

#### TypingIndicator
```
- Three dots in a row, staggered pulse animation
- Container: same style as AI message bubble but smaller
- Text below: "ბუნდოვანი კანონი ფიქრობს..." (Fuzzzy Law is thinking...)
```

#### CitationChip
```
- Inline tappable chip within AI messages
- Background: info-bg
- Text: info (body-small, semibold)
- Icon: paragraph symbol (§) or book icon (left)
- Format: "მუხ. 316 სამოქ. კოდ." (Art. 316 Civil Code)
- On tap: opens bottom sheet with full article text
- Long press: copy citation text
```

### 2. Law Browser Components

#### LawCodeCard
```
- Full-width card with elevation-1
- Left accent: 4px colored bar (different color per legal domain)
- Title: headline-medium (Georgian name)
- Subtitle: body-medium (English name, article count)
- Right: chevron icon
- On tap: navigate to code structure view
```

#### ArticleView
```
- Full article text with proper Georgian typography
- Article number: title-large, accent-500
- Article title: headline-medium
- Body: body-large, 1.6 line height for readability
- Paragraph numbers: highlighted in accent-400
- Cross-references: tappable links (underlined, info color)
- Top bar: Copy All | Save to Notes | Share buttons
```

### 3. Notes & Save Components

#### NoteCard
```
- Card with elevation-1, radius-lg
- Top: note title (auto-generated from content, editable)
- Body: preview of saved content (3 lines max, truncated)
- Source badge: "AI Response" | "Law Article" | "Personal Note"
- Bottom: date saved, legal domain tag chips
- Swipe actions: Edit, Delete
- Long press: multi-select mode
```

#### SaveToNotesSheet (Bottom Sheet)
```
- Triggered when user taps bookmark/save icon on any content
- Title field: auto-filled, editable
- Tags: auto-suggested legal domain tags (tappable to add/remove)
- Category picker: "AI Responses" | "Law Articles" | "My Notes"
- Content preview: shows what will be saved
- "Add Personal Note" text field: user can annotate
- Save button: accent-500, full width
- All notes stored locally (SQLite/Hive) — no server sync needed
```

#### NotesListScreen
```
- Search bar at top (searches note titles and content)
- Filter chips: All | AI Responses | Law Articles | My Notes
- Sort: Newest | Oldest | By Domain
- List of NoteCards
- FAB: "+" to create a new personal note
- Empty state: illustration + "Save your first note" message
```

#### NoteDetailScreen
```
- Full content view with rich formatting preserved
- Edit mode toggle (pencil icon in app bar)
- Personal annotations section (user's own notes about this content)
- Source link: tappable link back to original conversation or article
- Copy button: copies formatted content to clipboard
- Share button: share as text or PDF
- Delete button: in overflow menu
```

### 4. Intake Flow Components

#### IntakeQuestionCard
```
- Centered card with Georgian question text
- Progress indicator: horizontal dots showing current step
- Large text area for answer
- "Skip" button (text, neutral-400) + "Continue" button (filled, accent-500)
- Animated transition between questions (horizontal slide)
```

### 5. Analysis Result Components

#### AnalysisSection
```
- Collapsible sections with emoji headers:
  📋 SITUATION SUMMARY
  ⚖️ APPLICABLE LAWS  
  🛡️ RECOMMENDED STRATEGY
  📊 ALTERNATIVES
  ⚠️ RISKS
  📅 NEXT STEPS
  📚 CITATIONS
- Each section: card with left accent bar
- "Copy Section" and "Save Section to Notes" buttons per section
- Expand/collapse animation: 250ms, ease-out
```

#### StrategyCard
```
- Card showing one legal strategy
- Header: strategy name + confidence badge (High/Medium/Low)
- Body: plain-language explanation
- Pros/Cons list with green/red icons
- "Learn More" expandable section with law citations
- Copy and Save actions
```

---

## Screen Specifications

### Screen Map

```
app/
├── Splash Screen
├── Onboarding (3 pages — first launch only)
├── Home (Tab Navigation)
│   ├── Tab 1: Chat
│   │   ├── Conversation List
│   │   ├── Chat Screen (with intake flow)
│   │   └── Analysis Results
│   ├── Tab 2: Laws
│   │   ├── Law Codes List
│   │   ├── Code Structure (books/chapters)
│   │   ├── Article Detail
│   │   └── Search Results
│   ├── Tab 3: Notes
│   │   ├── Notes List
│   │   ├── Note Detail
│   │   └── Create/Edit Note  
│   └── Tab 4: Profile
│       ├── Settings
│       ├── Language Toggle
│       └── About / Disclaimer
└── Bottom Sheets
    ├── Citation Detail
    ├── Save to Notes
    └── Article Preview
```

### S1 — Splash Screen
```
- Dark background (primary-900)
- Centered logo with subtle scale animation (0.9 → 1.0, 800ms, spring curve)
- App name below logo with fade-in (delayed 300ms)
- Auto-navigate to Home after 1.5s (or Onboarding if first launch)
```

### S2 — Onboarding (3 Pages)
```
Page 1: "Ask Any Legal Question"
- Illustration: person talking to AI with speech bubbles
- Headline: "დასვით ნებისმიერი იურიდიული კითხვა"
- Body: "აღწერეთ თქვენი სიტუაცია ჩვეულებრივი სიტყვებით — ჩვენ ვიპოვით საჭირო კანონებს"

Page 2: "Get Every Applicable Law"  
- Illustration: stack of law books with search magnifier
- Headline: "მიიღეთ ყველა შესაბამისი კანონი"
- Body: "საქართველოს ყველა კოდექსი და კანონი — ერთ აპლიკაციაში"

Page 3: "Your Optimal Strategy"
- Illustration: shield with checkmark
- Headline: "თქვენი ოპტიმალური სტრატეგია"
- Body: "AI გთავაზობთ საუკეთესო სამართლებრივ გზას — გასაგები ენით"

Navigation: dot indicators + "Skip" + "Next" / "Get Started" on last page
```

### S3 — Home / Conversation List
```
- App bar: logo + "ბუნდოვანი კანონი" title
- Search bar below app bar
- List of past conversations:
  - Title (auto-generated from first message)
  - Preview of last message (1 line)
  - Date + legal domain badge
  - Unread indicator if AI responded while away
- FAB: "+" new conversation (accent-500, scale animation on press)
- Empty state: "დაიწყეთ პირველი კონსულტაცია" with illustration
```

### S4 — Chat Screen
```
- App bar: conversation title + overflow menu (Delete, Export, Save All to Notes)
- Message list: alternating user/AI bubbles
- AI messages have: copy button, save-to-notes bookmark icon
- Citation chips are tappable (open bottom sheet with full article)
- Intake questions appear as special cards (not regular messages)
- Chat input bar at bottom
- Keyboard-aware (input bar rises above keyboard)
```

### S5 — Notes Screen
```
- App bar: "ჩანაწერები" (Notes) + search icon
- Filter chips row (scrollable): All | AI | Laws | Personal
- Grid or list toggle
- Notes listed as NoteCards (see component spec above)
- FAB: create new personal note
- Swipe to delete with undo snackbar
- Notes are stored 100% locally (SQLite or Hive)
```

### S6 — Law Browser
```
- App bar: "კანონები" (Laws) + search icon  
- Search bar: full-text search across all laws
- Categories grid (2 columns):
  - Criminal Law (red accent)
  - Civil Law (blue accent)
  - Administrative (green accent)
  - Labor (orange accent)
  - Tax (purple accent)
  - Family (pink accent)
  - Property (teal accent)
  - Other (neutral accent)
- Below: list of all legal codes (LawCodeCards)
- Each code expands into book → chapter → article hierarchy
```

---

## Dark Mode

The app MUST support both light and dark modes, following system preference by default with a manual toggle in settings.

**Dark mode principles:**
- Never use pure black (#000000) — use primary-900 (#0A1628) as base
- Reduce white to neutral-100 for text
- Cards: dark-surface-1 → dark-surface-2 → dark-surface-3 (progressive elevation)
- Accent colors remain the same but slightly desaturated
- Borders become more important (use dark-border color)
- Shadows are replaced by subtle border + background differentiation

---

## Accessibility

- Minimum touch target: 48x48dp
- Minimum text contrast: 4.5:1 (WCAG AA)
- Support dynamic type / font scaling
- Screen reader labels on all interactive elements (Georgian + English)
- Reduce motion option (disables all animations)

---

## Localization

The app supports two languages:
1. **Georgian (ქართული)** — Primary, default
2. **English** — Secondary

All strings must be externalized. Use Flutter's `intl` package or equivalent.

---

## Iconography

Use a consistent icon set throughout:
- **Primary set:** Material Symbols (Outlined, weight 300)
- **Custom icons:** Scales of justice, Georgian paragraph symbol, legal gavel
- Icon size: 24dp (standard), 20dp (dense), 28dp (prominent)
- Icon color: follows text color of context

---

## Key UX Flows

### Flow 1: First Legal Consultation
```
Open App → Onboarding (first time) → Tap "+" New Conversation 
→ AI greeting: "გამარჯობა! რით შემიძლია დაგეხმაროთ?"
→ User describes problem in free text
→ AI asks clarifying questions (intake flow cards)
→ User answers each question
→ AI shows thinking indicator ("ვეძებ შესაბამის კანონებს...")
→ AI presents structured analysis with citations
→ User taps citation chip → sees full article text
→ User taps bookmark → saves response to notes
→ User can continue asking follow-up questions
```

### Flow 2: Browse & Save Laws
```
Tap "Laws" tab → Browse categories or search
→ Tap a legal code → See structure (books/chapters)
→ Tap an article → Read full text
→ Tap "Save to Notes" → Add personal annotation → Save
→ Go to Notes tab → Find saved article with annotation
```

### Flow 3: Review Saved Notes
```
Tap "Notes" tab → See all saved items
→ Filter by type (AI Responses / Laws / Personal)
→ Tap a note → View full content
→ Tap edit → Add/modify personal annotations
→ Tap copy → Content copied to clipboard
→ Tap share → Share as formatted text
```

---

## Deliverables Checklist

- [ ] Complete design token definitions (colors, typography, spacing, motion)
- [ ] Component specifications for all UI elements
- [ ] Screen mockups for all screens (S1-S6+)
- [ ] Dark mode variants for all screens
- [ ] UX flow diagrams for core user journeys
- [ ] Icon and illustration specifications
- [ ] Accessibility compliance notes
- [ ] Localization string structure (KA + EN)
- [ ] Notes system: local storage, CRUD, search, copy, share
- [ ] Animation specifications for all micro-interactions
