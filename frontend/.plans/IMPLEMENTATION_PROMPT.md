# Implementation Prompt — Full Production App

---

## 🔽 COPY FROM HERE 🔽

---

# Task: Build "Fuzzzy Law" — Full Production Flutter App

You are building a COMPLETE, PRODUCTION-READY Flutter mobile app called **ბუნდოვანი კანონი (Fuzzzy Law)** — an AI-powered legal case workspace for Georgian citizens. 

**No placeholders. No "coming soon." Every screen fully functional. One tap launch.**

This is an incremental but complete build. Work through each step fully before moving to the next. Every feature must be implemented, styled, wired, and working.

---

## MANDATORY: Read These Files First (IN THIS ORDER)

Before writing ANY code, you MUST read all of these:

1. **`frontend/.plans/SPEC.md`** — The canonical product spec. Every screen, every interaction, every principle. This is your bible. DO NOT deviate from it.

2. **`frontend/.agents/general_guide/flutter_architecture.md`** — Architecture rules. Feature folder structure, BLoC/Cubit patterns, DI, barrel files, error handling. NEVER violate these.

3. **`frontend/.agents/general_guide/lessons_learned.md`** — Anti-patterns and historical bugs. Repositories never throw. Cubits never try/catch. Single barrel import rule.

4. **`packages/open-design/design-systems/fuzzzy-law/DESIGN.md`** — Full visual design spec (one directory up from `frontend/`).

5. **`.agents/context/backend.md`** — Backend API (25 endpoints). All endpoint paths, auth, credit system (at project root level).

6. **`.agents/context/law_corpus.md`** — Law corpus details. 9,450 chunks, ChromaDB, metadata structure (at project root level).

---

## Project State — What Exists

**Package:** `fuzzzy_law` | **Bundle:** `ge.fuzzycore.fuzzzylaw` | **Flutter:** 3.32.0 (FVM)

**Already built (DO NOT recreate):**
- App shell: `FuzzzyLawApp`, `Initializer`, `GlobalBlocProviders`
- Core: DI (GetIt), HTTP client (Dio), error handling, l10n (ka/en), services (logger, cache, secure storage, dev panel)
- UI Kit package: `packages/ui_kit/` with theme extension system (`UiColors`, `UiTextStyles`, `UiFormStyles` via `context.uiColors` etc.)
- GoRouter skeleton (empty routes in `fuzzzy_law_router.dart`)
- BLoC generic states: `StateStatus`, `ActionStateStatus` enums

**Not built yet (YOU BUILD THIS):**
- No `features/` directory — create from scratch
- No routes configured — implement GoRouter navigation
- UI Kit has placeholder colors/fonts (TODO comments) — inject real design tokens
- No screens, no features, no models

**Key dependencies already in pubspec:**
`flutter_bloc`, `go_router`, `get_it`, `dio`, `hive`/`hive_flutter`, `flutter_dotenv`, `url_launcher`, `shimmer`, `google_fonts` (just added), `flutter_svg`, `permission_handler`, `package_info_plus`, `shared_preferences`

---

## Backend API Available

The backend is LIVE. Connect to it via the HTTP client.

**Key endpoints to integrate:**

| Endpoint | Method | Credits | Use For |
|----------|--------|---------|---------|
| `/api/v1/auth/verify-token` | POST | 0 | Firebase auth |
| `/api/v1/conversations` | POST | 0 | Start AI conversation |
| `/api/v1/conversations` | GET | 0 | List conversations |
| `/api/v1/conversations/{id}` | GET | 0 | Get conversation with messages |
| `/api/v1/chat/{id}/send` | POST | 1 | Send message → AI response with citations |
| `/api/v1/chat/{id}/ws` | WS | 1 | WebSocket streaming chat |
| `/api/v1/case-files/build` | POST | 3 | Build full defense case file |
| `/api/v1/case-files` | GET | 0 | List case files |
| `/api/v1/case-files/{id}` | GET | 0 | Get case file detail |
| `/api/v1/case-files/{id}` | PATCH | 0 | Update case notes/status |
| `/api/v1/laws/search?q=...` | GET | 0 | Search laws (free) |
| `/api/v1/laws/codes` | GET | 0 | List legal codes |
| `/api/v1/laws/codes/{id}` | GET | 0 | Code structure (chapters/articles) |
| `/api/v1/laws/articles/{id}` | GET | 0 | Full article text |
| `/api/v1/account/credits` | GET | 0 | Credit balance |

**Auth:** Firebase ID token in Authorization header. Dev mode: no token needed, mock ADMIN user.

**AI response format:** Messages contain `citation_text` patterns like `მუხლი 316` that link to corpus chunks with `article_url` (matsne.gov.ge deep links) and full article text.

---

## BUILD ORDER — Follow Exactly

### Step 1: UI Kit Design Tokens

Update ALL existing UI Kit files with the legal app design system.

**Color palette:**
```dart
// Dark theme (DEFAULT)
backgroundPrimary:    Color(0xFF0A1628)  // Deep navy
backgroundSecondary:  Color(0xFF121E32)  // Card surface
accent:               Color(0xFFD4A84B)  // Warm gold
textPrimary:          Color(0xFFF0EDE8)  // Warm off-white
textSecondary:        Color(0xFF8B95A5)  // Muted
error:                Color(0xFFE5534B)  // Red
success:              Color(0xFF4CAF79)  // Green
warning:              Color(0xFFE8A838)  // Amber
info:                 Color(0xFF5B9BD5)  // Blue

// Trust level colors (for AI messages)
verified:             Color(0xFF4CAF79)  // Green — verified citation
interpretation:       Color(0xFFE8A838)  // Amber — AI interpretation
guidance:             Color(0xFF5B9BD5)  // Blue — general guidance

// Legal domain colors
criminal:             Color(0xFFE5534B)  // Red
civil:                Color(0xFF5B9BD5)  // Blue
administrative:       Color(0xFF4CAF79)  // Green
labor:                Color(0xFFE8A838)  // Orange/amber
tax:                  Color(0xFF9B72CF)  // Purple
family:               Color(0xFFE88BA8)  // Pink
property:             Color(0xFF4DB6AC)  // Teal
other:                Color(0xFF8B95A5)  // Gray

// Light theme
backgroundPrimary:    Color(0xFFF5F3EF)  // Warm off-white
backgroundSecondary:  Color(0xFFFFFFFF)  // White cards
accent:               Color(0xFFB8892E)  // Darker gold
textPrimary:          Color(0xFF1A1A2E)  // Near black
textSecondary:        Color(0xFF6B7280)  // Gray
```

**Typography with Google Fonts:**
- Georgian body: `GoogleFonts.notoSansGeorgian()`
- Latin body: `GoogleFonts.inter()`
- Legal citations: `GoogleFonts.jetBrainsMono()`
- Georgian text MUST have `height: 1.55` for readability
- Add `google_fonts` dependency to `packages/ui_kit/pubspec.yaml` too

**Update these files:**
- `packages/ui_kit/lib/src/colors/ui_kit_colors.dart`
- `packages/ui_kit/lib/src/themes/theme_extensions/ui_colors.dart` — Add fields: `accentColor`, `successColor`, `warningColor`, `infoColor`, `surfaceColor` + all trust level + domain colors
- `packages/ui_kit/lib/src/text_styles/ui_kit_text_styles.dart` — Use Google Fonts
- `packages/ui_kit/lib/src/themes/ui_kit_theme.dart` — Wire everything, dark default

---

### Step 2: Navigation Shell — 3 Tabs + Case Sub-Routes

**Build the full GoRouter configuration with:**
- `StatefulShellRoute.indexedStack` for 3 bottom tabs
- `MainShell` widget with `BottomNavigationBar` (3 tabs: Cases, Laws, Profile)
- Case workspace uses nested navigation for sub-sections
- Tab labels in Georgian: საქმეები, კანონები, პროფილი

**Full route tree:**
```
/                           → redirect to /cases
/cases                      → MyCasesPage
/cases/:id                  → CaseWorkspacePage (default: overview)
/cases/:id/overview
/cases/:id/chat
/cases/:id/chat/:conversationId
/cases/:id/facts
/cases/:id/arguments
/cases/:id/evidence
/cases/:id/strategy
/cases/:id/timeline
/cases/:id/risks
/laws                       → LawsHomePage
/laws/search?q=             → LawSearchResultsPage
/laws/:codeId               → CodeStructurePage
/laws/:codeId/:articleId    → ArticleDetailPage
/profile                    → ProfilePage
```

---

### Step 3: Cases Feature — FULL Implementation

This is the heart of the app. Build COMPLETELY.

**Models:**
```dart
class CaseData {
  final String id;
  final String title;
  final LegalDomain domain;
  final CaseStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<FactData> facts;
  final List<ArgumentData> arguments;
  final List<EvidenceData> evidence;
  final StrategyData? strategy;
  final List<TimelineEventData> timeline;
  final List<RiskData> risks;
  final List<ActionItemData> actionItems;
  final List<String> linkedConversationIds;
  // completeness calculated from filled sections
}

class FactData {
  final String id;
  final String text;
  final FactClassification classification; // favorable, unfavorable, neutral
  final String? sourceDocumentId;
  final String? sourceConversationId;
  final String? linkedArgumentId;
  final bool isAiGenerated;
  final DateTime createdAt;
}

class ArgumentData {
  final String id;
  final String title;
  final String explanation;
  final ArgumentStrength strength; // strong, moderate, weak
  final List<String> linkedArticleIds; // law article references
  final List<String> linkedFactIds;
  final List<String> linkedEvidenceIds;
  final bool isAiGenerated;
  final DateTime createdAt;
}

class EvidenceData {
  final String id;
  final String title;
  final String? filePath;
  final EvidenceType type; // document, photo, screenshot, receipt, other
  final String? linkedFactId;
  final DateTime addedAt;
}

class StrategyData {
  final String primaryStrategy;
  final String? backupStrategy;
  final String? fallbackPosition;
  final int confidenceScore; // 0-100
  final List<String> supportingArgumentIds;
  final List<String> supportingArticleIds;
  final bool isAiGenerated;
}

class TimelineEventData {
  final String id;
  final DateTime date;
  final String title;
  final String? description;
  final TimelineEventType type; // past, deadline, milestone
  final bool isCompleted;
}

class RiskData {
  final String id;
  final String description;
  final RiskSeverity severity; // high, medium, low
  final String? mitigationSuggestion;
  final String? linkedArticleId;
  final bool isAiGenerated;
}

class ActionItemData {
  final String id;
  final String task;
  final DateTime? deadline;
  final ActionPriority priority; // high, medium, low
  final bool isCompleted;
}
```

Store cases in **Hive** (local-first). Each case is a HiveObject with TypeAdapters for all models.

**Pages to build (FULLY FUNCTIONAL):**

1. **MyCasesPage** — List of all cases with:
   - Empty state (icon + message + CTA button, as shown in SPEC.md)
   - Case cards with: title, domain chip (colored), status badge, completeness bar, last updated
   - FAB "+" → triggers NewCaseSheet
   - Swipe to archive
   - Pull to refresh

2. **NewCaseSheet** — Bottom sheet with:
   - Text field for case title
   - Domain picker grid (8 legal domains with colored dots)
   - "შექმნა" (Create) button → creates case → navigates to workspace

3. **CaseWorkspacePage** — Container with:
   - App bar: back arrow, case title (editable), overflow menu (export, archive, delete)
   - Status + domain display
   - Completeness ring/bar
   - Horizontal scrollable `TabBar` with 8 tabs
   - `TabBarView` showing the active section

4. **CaseOverviewSection** — Bird's-eye dashboard with:
   - Completeness percentage
   - Summary stat cards (facts count, arguments count, evidence count, risks count)
   - Defense strategy summary card (tappable)
   - Upcoming deadlines card with countdown + urgency colors
   - Action items (next 3, with checkboxes)
   - Latest AI consultation summary (tappable → goes to chat)
   - Case strength meter (calculated from data completeness)
   - ALL cards tappable → navigate to corresponding tab

5. **CaseFactsSection** — Full facts management:
   - Segment control: Favorable ✅ / Unfavorable ❌ / Neutral ℹ️
   - Fact cards with: text, source links (document/conversation), linked argument badge
   - AI-extracted badge where applicable
   - Add fact: text field + classification picker + optional source link
   - Edit/delete facts
   - Each fact shows related argument and risk links

6. **CaseArgumentsSection** — Full argument management:
   - Numbered argument cards with: title, explanation, strength badge (Strong/Moderate/Weak with color)
   - Linked law article citation chips (tappable → article bottom sheet → matsne.gov.ge)
   - Linked facts and evidence badges
   - **Guided argument builder** (NOT blank text field):
     - Step 1: "What happened?" → free text
     - Step 2: "Which law?" → AI suggests articles, user confirms
     - Step 3: "Evidence?" → link existing evidence
     - AI evaluates strength automatically
   - Counter-argument section: "What the other side may argue" + prepared response

7. **CaseEvidenceSection** — Evidence management:
   - Grid/list of attached items with thumbnails/icons
   - Each item: title, type icon, date, linked fact badge
   - Add evidence: camera, gallery, file picker (use `permission_handler`)
   - Evidence detail: preview + metadata + linked facts/arguments
   - Admissibility indicator with explanation

8. **CaseStrategySection** — Defense strategy:
   - Primary strategy card (editable)
   - Backup strategy card (editable)
   - Fallback position card (editable)
   - Confidence rating per strategy
   - Supporting arguments and law article links
   - AI-generated badge where applicable
   - "Regenerate with AI" button (costs credits)

9. **CaseTimelineSection** — Timeline + deadlines:
   - Vertical timeline visualization
   - Each event: date, title, description, type icon (past ✓, deadline ⏰, milestone ⭐)
   - Deadline events: countdown display, urgency color (🔴 < 7 days, 🟡 < 30, 🟢 > 30)
   - Add event: date picker + title + type
   - Statute of limitations warning card (when applicable)
   - Procedural compliance checklist (filing deadlines, court fees, documents)

10. **CaseRisksSection** — Risks + weaknesses:
    - Risk cards with: description, severity badge (High/Medium/Low with color), mitigation suggestion
    - Linked law articles where applicable
    - AI-generated badge
    - Add risk manually
    - "Red Team" button: AI generates counter-arguments against the user's position

---

### Step 4: AI Consultation Feature — FULL Implementation

Build the in-case AI chat that connects to the backend.

**Data source:** Connect to backend endpoints:
- `POST /api/v1/conversations` — create conversation linked to case
- `POST /api/v1/chat/{id}/send` — send message, get AI response
- `GET /api/v1/conversations/{id}` — get conversation history

**Chat UI (inside CaseWorkspacePage chat tab):**

1. **Context banner** at top showing case context:
   ```
   📁 8 ფაქტი · 5 არგუმენტი · 4 დოკუმენტი
   ```

2. **Message list** — scrollable, AI messages left, user messages right

3. **AI message bubble** with:
   - Trust level indicator (green/amber/blue left border)
   - Message text with inline **citation chips** (`[§ მუხ. 316 სამოქ. კოდ.]`)
   - Verification badge: "✅ N ციტატა დადასტურებულია"
   - Quick-add buttons: `[+ ფაქტებში]` `[+ არგუმენტში]`
   - Auto-classification banner when AI detects new fact/deadline

4. **User message bubble** — accent-colored, right-aligned, max 80% width

5. **Chat input bar** — pill shape, floating above content:
   - Text field: "აღწერეთ ახალი გარემოება..."
   - Attachment button (📎)
   - Send button (accent colored, arrow icon)
   - Expands for multiline

6. **Typing indicator** — three dots, pulsing animation

7. **Citation chip tap** → Bottom sheet with:
   - Article title + code name
   - Full article text (from API response)
   - "💡 რას ნიშნავს" plain-language explanation
   - `[🔗 matsne.gov.ge-ზე ნახვა]` — opens `url_launcher` with `article_url`
   - `[📁 საქმეში დამატება]` — add to case's applicable laws
   - `[📋 კოპირება]` — copy article text

8. **Referral card** — when AI can't find applicable law:
   - Clear message: "ეს საკითხი მოითხოვს დამატებით ინფორმაციას"
   - Relevant institution from directory (name, phone, address, hours)
   - Pre-written question user can read aloud
   - Copy button for the question
   - Fallback link to matsne.gov.ge search

---

### Step 5: Laws Browser — FULL Implementation

Connect to backend law endpoints (all free, no credits).

1. **LawsHomePage** — Category grid (2 columns):
   - 8 legal domain cards with colored accent dots
   - Each card: domain name (Georgian), article count, right chevron
   - Search bar at top → navigates to search results

2. **CodeStructurePage** — Hierarchical view:
   - Code title, total articles
   - Expandable chapters/sections → article list

3. **ArticleDetailPage** — Full article view:
   - Article number in accent color
   - Full legal text with Noto Sans Georgian, `height: 1.6`
   - **"💡 რას ნიშნავს ეს თქვენთვის"** (What this means for you) — plain-language box
   - **Legal term tooltips** — jargon words have ℹ️ icon, tap for explanation
   - `[📁 საქმეში დამატება]` — pick which case → which section
   - `[🔗 matsne.gov.ge-ზე ნახვა]` — open official source
   - `[📋 კოპირება]` — copy text
   - Cross-reference links to related articles

4. **LawSearchResultsPage** — Search results:
   - Connected to `GET /api/v1/laws/search?q=...`
   - Result cards: article number, code name, text snippet, domain color
   - Tap → ArticleDetailPage

---

### Step 6: Profile — FULL Implementation

1. **ProfilePage:**
   - User info card (email if authenticated, "Guest" otherwise)
   - Credit balance display (from `GET /api/v1/account/credits`)
   - Plan badge: FREE / PRO
   - **Language toggle** — working KA ↔ EN switch (uses existing `LocalizationCubit`)
   - **Theme toggle** — working Dark ↔ Light switch (uses existing `ThemeCubit`)
   - Legal glossary link (searchable list of ~50 legal terms with plain-language Georgian explanations)
   - Court etiquette guide (simple, warm guide for first-timers)
   - Legal disclaimer
   - App version (from `package_info_plus`)
   - About section

2. **LegalGlossaryPage** — Searchable list:
   - ~50 common Georgian legal terms
   - Each term: Georgian word, plain-language explanation, English equivalent
   - Search bar for filtering

3. **CourtGuidePage** — Simple guide:
   - How to address the judge
   - What to bring
   - What to wear
   - When to speak
   - Timeline of a court session

---

### Step 7: Case Export

From case overview → export button:

1. Generate structured text summary of entire case
2. Sections: Situation, Facts (categorized), Arguments (with citations), Strategy, Evidence list, Timeline, Risks, Action items
3. Each citation includes matsne.gov.ge URL
4. Copy to clipboard OR share via system share sheet
5. Case strength score at the top

---

### Step 8: Wire Everything Together

1. Add `export 'features/features.dart';` to `src.dart`
2. Register ALL cubits and repositories in `dependency_injection.dart`
3. Initialize Hive with all TypeAdapters in `Initializer.preAppInit()`
4. Configure ALL routes in `fuzzzy_law_router.dart`
5. Add ALL new localization strings via `loc.sh` pattern (externalize every user-facing string)
6. Remind user to run `./exp.sh` after all file creation

---

## Architecture Rules — NEVER VIOLATE

1. **Repositories return sealed classes** (`Success | Failure`), NEVER throw
2. **Cubits use exhaustive switch**, NEVER try/catch
3. **Constructor injection** for repos and cubits. `sl.get<T>()` ONLY in data sources
4. **No hardcoded colors** — use `context.uiColors.accentColor` etc.
5. **No hardcoded text styles** — use `context.uiTextStyles.bodyBold16` etc.
6. **Single import** — `import 'package:fuzzzy_law/src/src.dart';`
7. **Every directory gets a barrel file** exporting all children
8. **State is immutable** — always `copyWith`
9. **Dark mode is default** — test dark first
10. **Georgian text uses Noto Sans Georgian** with `height: 1.55`
11. **48×48dp minimum touch targets**
12. **No pure black backgrounds** — always navy-tinted

## Visual Design Rules

1. Dark navy `#0A1628` background, card surface `#121E32`, accent gold `#D4A84B`
2. Bottom nav: active = gold icon + label, inactive = muted icon only
3. Case cards: subtle border, domain-color 4px left accent bar, 12px rounded corners
4. Citation chips: info-tinted background, § icon, tappable
5. Trust level borders: 3px left border (green/amber/blue)
6. Fact cards: classification-colored left accent (green/red/blue)
7. No gradients on cards/buttons
8. Accent color max 2 elements per screen
9. Smooth animations: 150ms message slide-in, 250ms section expand, 300ms screen transitions
10. Shimmer loading states on all async content

## Expected Output

When complete, the app MUST:
1. Launch to an elegant dark-themed Cases home screen
2. Create cases with name + legal domain
3. Open case workspace with 8 fully functional sub-tabs
4. Show bird's-eye overview with live data from all sections
5. Run AI chat with backend, showing citation chips that open matsne.gov.ge
6. Manage facts with favorable/unfavorable/neutral categorization
7. Build arguments through guided flow with linked law articles
8. Attach evidence (photos/files) linked to facts
9. Show defense strategy with confidence ratings
10. Display timeline with deadline countdowns and urgency colors
11. Assess risks with severity and mitigation
12. Browse Georgian law codes from backend API
13. View articles with plain-language explanations and matsne.gov.ge links
14. Add articles to cases from the law browser
15. Toggle language (KA/EN) and theme (dark/light) from profile
16. Export case summary to clipboard
17. Show referral cards when AI doesn't have an answer
18. Display legal glossary and court etiquette guide
19. Handle loading/error/empty states gracefully with shimmer and retry
20. Pass `flutter analyze` with zero errors

After implementation, tell the user to run:
```bash
./exp.sh
flutter pub get
flutter analyze
flutter run
```

---

## 🔼 COPY UNTIL HERE 🔼
