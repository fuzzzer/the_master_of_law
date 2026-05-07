# Task: Run Flutter App on Web & E2E User Testing

> **Goal:** Launch the Flutter app on Chrome (web), visually walk through every screen and interaction as a real user would. Document what works, what's broken, what's missing UI, and what's just a placeholder. This is a full app audit through the eyes of a user.

---

## Prerequisites — Environment Setup

### 1. Flutter SDK (FVM)

The project uses FVM with Flutter `3.32.0`. All flutter commands should use the FVM-managed SDK.

```bash
cd /Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/frontend

# Verify FVM is installed and correct version is active
fvm use 3.32.0
fvm flutter --version  # Should show 3.32.0
```

### 2. Dependencies

```bash
cd /Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/frontend
fvm flutter pub get
```

### 3. Backend (Optional — for API-connected features)

If you need to test features that call the backend API (chat, laws browser, etc.):

```bash
cd /Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

> **Note:** The backend runs in dev mode (no Firebase auth required, mock ADMIN user).
> `env/env.development` has `BASE_URI=http://127.0.0.1:8000`.

### 4. Launch Flutter Web

```bash
cd /Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/frontend
fvm flutter run -d chrome --web-port 8080
```

If `fvm` is not available, try:
```bash
flutter run -d chrome --web-port 8080
```

**Wait for:** `The web application was compiled successfully` message. Note the URL (likely `http://localhost:8080`).

---

## Phase 1: App Launch & First Impression

### 1.1 — Does it compile and launch?

- [ ] `flutter run -d chrome` succeeds without compile errors
- [ ] Browser opens and shows the app
- [ ] No white screen / blank page / console crash

**If compilation fails:**
- Capture the full error output
- Check if it's a web-specific issue (packages like `flutter_secure_storage`, `permission_handler` may have web-incompatible code)
- Check `lib/src/core/dependency_injection_web.dart` — this should handle web-specific DI
- Document the error and stop — this is a **blocking issue**

### 1.2 — Initial rendering

- [ ] App title visible: **კანონის ოსტატი**
- [ ] Bottom navigation bar renders with 3 tabs
- [ ] Correct tab labels: **საქმეები** (Cases), **კანონები** (Laws), **პროფილი** (Profile)
- [ ] Tab icons render (folder, book, person)
- [ ] Default tab is Cases (`/cases` route)
- [ ] Dark theme / light theme renders properly (check `UiKitTheme`)
- [ ] Georgian text renders correctly (Mkhedruli script, no □□□ boxes)

**Screenshot:** Capture the initial landing page.

### 1.3 — Web-specific UX

- [ ] Responsive layout — does it look acceptable at desktop width?
- [ ] No horizontal overflow / scroll issues
- [ ] Fonts load (Google Fonts — may require internet)
- [ ] No console errors in Chrome DevTools

---

## Phase 2: Cases Tab (საქმეები) — Primary Feature

The Cases tab is at `/cases`. Cases = Projects. This is the core of the app.

### 2.1 — Empty state

When no cases exist:

- [ ] Empty state illustration/icon renders (⚖️ balance icon, 72px)
- [ ] Georgian text: "თქვენ ჯერ არ გაქვთ საქმე" (You don't have any cases yet)
- [ ] Subtitle: "შექმენით პირველი საქმე და AI დაგეხმარებათ მის მოწყობაში"
- [ ] CTA button: "ახალი საქმის შექმნა" (Create new case) — renders, is tappable
- [ ] Secondary link: "ან შეისწავლეთ კანონები →" — renders
- [ ] FAB is hidden when empty state is shown

### 2.2 — Create new case (bottom sheet)

Tap "ახალი საქმის შექმნა":

- [ ] Bottom sheet slides up with rounded top corners
- [ ] Sheet has a form for entering case title
- [ ] Can type Georgian text in the input field
- [ ] Submit creates a case and sheet dismisses
- [ ] New case appears in the list
- [ ] Error handling if creation fails

### 2.3 — Case list

After creating 2-3 cases:

- [ ] Cases render as cards (`CaseCard` widget)
- [ ] Card shows case title
- [ ] Card shows any metadata (date, status, category)
- [ ] Cards are tappable → navigates to case detail
- [ ] Swipe-to-dismiss works (delete case)
- [ ] Pull-to-refresh works
- [ ] FAB (+) appears when list is non-empty
- [ ] Search icon in AppBar — does it do anything?

### 2.4 — Case workspace (detail page)

Tap on a case card → navigates to `/cases/:caseId`:

- [ ] `CaseWorkspacePage` renders
- [ ] Case title shown
- [ ] Case sections are visible (the app has a case-centric architecture with up to 9 sections)
- [ ] Can edit case sections
- [ ] Navigation back to cases list works (back button / back gesture)
- [ ] Any AI-powered features visible? (case builder, legal analysis)

### 2.5 — Data persistence

- [ ] Close the browser tab and reopen → cases are still there (Hive local storage)
- [ ] Delete a case → it's gone after refresh

---

## Phase 3: Laws Tab (კანონები)

Navigate to the Laws tab (second tab in bottom nav).

### 3.1 — Laws home page

- [ ] `LawsHomePage` renders
- [ ] Shows list of legal codes (12 Georgian legal codes)
- [ ] Each code shows its name in Georgian
- [ ] Codes are tappable

**Note:** This tab uses `LawsRemoteDataSource` which calls the backend API (`GET /api/v1/laws/codes`). If backend is not running:
- [ ] Does it show an error state or loading forever?
- [ ] Is there offline / fallback handling?

### 3.2 — With backend running

If backend is running at `http://127.0.0.1:8000`:

- [ ] Codes list loads from API
- [ ] Can tap a code → shows code structure (articles)
- [ ] Can tap an article → shows article text
- [ ] Search functionality works (`GET /api/v1/laws/search?q=...`)
- [ ] Georgian text renders properly in article content

### 3.3 — Without backend

- [ ] Shows appropriate error/retry UI
- [ ] No unhandled exceptions or crashes

---

## Phase 4: Profile Tab (პროფილი)

Navigate to the Profile tab (third tab in bottom nav).

### 4.1 — Profile page rendering

- [ ] `ProfilePage` renders
- [ ] Shows user info section (or placeholder for unauthenticated)
- [ ] Theme toggle works (dark/light switch)
- [ ] Language selector works (ka/en localization)
- [ ] App version shown (from `package_info_plus`)
- [ ] Any settings/preferences visible

### 4.2 — Localization toggle

If language switching is available:

- [ ] Switch from Georgian to English
- [ ] All UI text updates across the app (tab labels, button text, headings)
- [ ] Switch back to Georgian — everything restores
- [ ] Localization files exist: `lib/src/core/l10n/`

### 4.3 — Theme toggle

- [ ] Switch between dark and light themes
- [ ] All screens update colors correctly
- [ ] No contrast issues (text readable on background)
- [ ] Bottom nav bar colors update

---

## Phase 5: Navigation & Routing

### 5.1 — Tab switching

- [ ] Tap Cases → Laws → Profile → Cases: each tab loads its content
- [ ] Tab state is preserved (StatefulShellRoute.indexedStack)
- [ ] If you create a case, switch to Laws, switch back — case list is still there

### 5.2 — Deep linking (GoRouter)

- [ ] Navigate to `/cases` directly in browser URL bar
- [ ] Navigate to `/laws` directly
- [ ] Navigate to `/profile` directly
- [ ] Navigate to `/cases/some-id` — does it try to load that case?
- [ ] Invalid route (e.g., `/nonexistent`) — what happens?

### 5.3 — Browser navigation

- [ ] Browser back/forward buttons work correctly
- [ ] URL updates when switching tabs
- [ ] Refresh page — app reloads to current route (not always back to `/cases`)

---

## Phase 6: Consultation/Chat Feature

Check if consultation (AI chat) is accessible from anywhere:

### 6.1 — Entry point

- [ ] Is there a chat button/entry point in the Cases workspace?
- [ ] Or is consultation a separate route?
- [ ] Check `/consultation` route

### 6.2 — Chat UI (if accessible)

- [ ] Message input field renders
- [ ] Can type Georgian text
- [ ] Send button is visible
- [ ] If backend is running: send a message → get AI response
- [ ] If backend is NOT running: error handling

### 6.3 — RAG source toggles (if implemented)

- [ ] Source toggle chips visible (📜 კანონები, ⚖️ პრაქტიკა, 🏛️ დიდი პალატა)
- [ ] Can toggle sources on/off
- [ ] State persists during conversation

---

## Phase 7: Web-Specific Issues

### 7.1 — Package compatibility

These packages may have web issues — check for each:

| Package | Web Support | Check |
|---------|------------|-------|
| `flutter_secure_storage` | ⚠️ Uses localStorage on web | [ ] No errors? |
| `permission_handler` | ❌ No web support | [ ] Import guarded? |
| `hive` / `hive_flutter` | ✅ Uses IndexedDB | [ ] Data persists? |
| `shake` | ❌ No web support | [ ] Import guarded? |
| `package_info_plus` | ✅ Supported | [ ] Version displays? |
| `google_fonts` | ✅ Supported | [ ] Fonts load? |
| `go_router` | ✅ Supported | [ ] Routing works? |

### 7.2 — Conditional imports

The app has conditional imports:
```dart
// dependency_injection.dart:6
import 'dependency_injection_web.dart' if (dart.library.io) 'dependency_injection_native.dart' as platform_di;
```

- [ ] `dependency_injection_web.dart` has proper web-safe implementations
- [ ] No `dart:io` imports leak into web builds

### 7.3 — Console errors

Open Chrome DevTools → Console tab:

- [ ] Document ALL console errors
- [ ] Document ALL console warnings
- [ ] Note any CORS issues when calling backend API

### 7.4 — Network requests

Open Chrome DevTools → Network tab:

- [ ] Font requests succeed (Google Fonts CDN)
- [ ] API calls to `127.0.0.1:8000` succeed (if backend running)
- [ ] No failed asset loads

---

## Phase 8: Responsive / Desktop Layout

Since this is running in a Chrome browser:

### 8.1 — Window sizes

Test at different browser widths:

- [ ] **Mobile (375px)** — bottom nav visible, content fits
- [ ] **Tablet (768px)** — no excessive whitespace or broken layout
- [ ] **Desktop (1440px)** — content is centered or fills appropriately
- [ ] **Very narrow (320px)** — no overflow errors

### 8.2 — Text overflow

- [ ] Long Georgian case titles don't overflow cards
- [ ] AppBar title doesn't overflow
- [ ] Bottom nav labels fit

---

## Deliverable — Test Report

After completing all phases, write a comprehensive report:

```markdown
# Flutter Web E2E Test Report — კანონის ოსტატი

## Environment
- Flutter version: X.X.X
- Browser: Chrome XX
- Backend: running / not running
- Date: YYYY-MM-DD

## Summary
- ✅ Working: X features
- ⚠️ Partial: X features  
- ❌ Broken: X features
- 🔲 Not yet implemented: X features

## Phase Results
### Phase 1: App Launch
...

### Phase 2: Cases
...

(etc.)

## Critical Issues (must fix before any user sees this)
1. ...
2. ...

## Minor Issues (should fix)
1. ...

## Not Implemented Yet (expected — matches project_status.md)
1. ...

## Screenshots
(embed any captured screenshots)
```

Save report to: `.tasks/reports/flutter_web_e2e_report.md`

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `frontend/lib/main.dart` | Entry point (dev) |
| `frontend/lib/src/app/themasteroflaw_app.dart` | App widget |
| `frontend/lib/src/app/navigation/themasteroflaw_router.dart` | GoRouter config (3 tabs) |
| `frontend/lib/src/app/navigation/main_shell.dart` | Bottom nav shell |
| `frontend/lib/src/features/cases/` | Cases feature (full scaffold) |
| `frontend/lib/src/features/laws/` | Laws browser feature |
| `frontend/lib/src/features/consultation/` | AI consultation/chat |
| `frontend/lib/src/features/profile/` | Profile & settings |
| `frontend/lib/src/core/dependency_injection.dart` | DI (has web guard) |
| `frontend/lib/src/core/dependency_injection_web.dart` | Web-specific DI |
| `frontend/packages/ui_kit/` | Design system package |
| `frontend/env/env.development` | `BASE_URI=http://127.0.0.1:8000` |
| `frontend/.fvm/fvm_config.json` | Flutter `3.32.0` |
| `backend/` | FastAPI backend (start with uvicorn) |

---

## Implementation Order for the Agent

1. **Setup** — Install deps, verify Flutter web toolchain (15 min)
2. **Launch** — `flutter run -d chrome` and verify compilation (10 min)
3. **Phase 1** — App launch, first impression, screenshot (10 min)
4. **Phase 2** — Cases tab: empty state, create, list, workspace (30 min)
5. **Phase 3** — Laws tab: with/without backend (20 min)
6. **Phase 4** — Profile tab: theme, locale, settings (15 min)
7. **Phase 5** — Navigation: tabs, deep links, browser nav (15 min)
8. **Phase 6** — Consultation/chat if reachable (15 min)
9. **Phase 7** — Web-specific: console errors, package compat (15 min)
10. **Phase 8** — Responsive: resize browser, check layouts (10 min)
11. **Report** — Write comprehensive test report (20 min)

**Total estimate:** ~3 hours

---

## Important Notes

- The project is named `themasteroflaw` in pubspec but displayed as `კანონის ოსტატი`
- Bundle ID: `ge.fuzzycore.masteroflaw`
- Package name in imports: `package:themasteroflaw/`
- The app currently has **3 tabs** (Cases, Laws, Profile), not the 5 originally planned (Chat and Notes tabs not yet added)
- Consultation feature exists as a feature module but may not be routed to a tab yet
- Backend runs in **dev mode** — no Firebase auth needed, uses mock ADMIN user
- Georgian text (UTF-8 Mkhedruli U+10D0–U+10FF) must render correctly everywhere
- Use `ui_kit` design tokens for theming — don't judge against external design specs
