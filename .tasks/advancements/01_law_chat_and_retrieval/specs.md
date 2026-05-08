# Specs: Simple Law-Aware Chat + Isolated Law Retrieval

---

## Behavioral Specifications

### Law Browser

| Behavior | Specification |
|----------|---------------|
| Codes list | Displays all 12 Georgian legal codes from `GET /laws/codes`. Name in Georgian, description in user's locale. |
| Code detail | Shows hierarchical article structure from `GET /laws/codes/{id}`. Expandable tree. |
| Article view | Renders full article text from `GET /laws/articles/{id}`. Preserves legal formatting (numbered paragraphs, sub-points). |
| Search | `GET /laws/search?q={query}` — minimum 2 characters. Debounced 300ms. Results show article title, code name, and snippet with highlighted match. |
| Empty state | "No results found" message in Georgian with suggestion to try different keywords. |
| Error state | Retry button + Georgian error message. Never show raw HTTP errors. |

### Law-Aware Chat

| Behavior | Specification |
|----------|---------------|
| RAG config | Always sends `{"legal_codes": true, "court_practice": false, "grand_chamber": false}` |
| Mode indicator | Visual badge/chip in chat header showing "კანონები" (Laws) mode |
| Response format | AI responses must include inline article citations (მუხლი N) |
| Citation tap | Tapping a citation navigates to `LawArticleScreen` with the referenced article |
| Credit cost | 1 credit per message (same as regular chat) |
| Input language | Accept Georgian and English input. Respond in Georgian. |

### Isolated Retrieval (Case Building Phase 1)

| Behavior | Specification |
|----------|---------------|
| Save to case | Any article or search result can be "attached" to an active case |
| Attachment model | Stores: `case_id`, `article_id`, `code_name`, `article_title`, `attached_at` |
| Case context | When launched from a case, shows "Adding laws to: [Case Name]" header |
| Standalone use | When launched from Laws tab, no case context — pure browsing |
| Max attachments | No hard limit, but UI warns after 20 articles per case |

---

## Technical Constraints

### Flutter Architecture
- Follow feature-first structure: `lib/features/laws/`
- Layers: `data/` (models, repositories) → `domain/` (if needed) → `presentation/` (cubit, screens, widgets)
- State management: Cubit (not Bloc) per existing project convention
- HTTP client: use the project's existing HTTP wrapper (check `lib/core/` for pattern)
- All user-facing strings must go through localization (`AppLocalizations`)

### API Contract (Backend — already exists)
```
GET  /api/v1/laws/codes           → List<LawCode>
GET  /api/v1/laws/codes/{id}      → LawCodeDetail (with articles tree)
GET  /api/v1/laws/articles/{id}   → ArticleDetail (full text)
GET  /api/v1/laws/search?q=...    → SearchResults (with snippets)
POST /api/v1/chat/{id}/send       → ChatResponse (with rag_config in body)
```

### Georgian Text Requirements
- All UI labels in Georgian (ka locale)
- UTF-8 throughout — Mkhedruli script (U+10D0–U+10FF)
- Article citations: pattern `მუხლი \d+` (Article N)
- Search must handle Georgian diacritics and compound words

### Performance
- Law codes list: cache locally after first fetch (codes don't change frequently)
- Article text: cache per session (same article viewed multiple times during research)
- Search: debounce input, show loading skeleton during fetch
- Chat: streaming via WebSocket preferred, fallback to HTTP POST

### Design
- Follow design tokens from `packages/open-design/design-systems/kanonis-ostati/DESIGN.md`
- Match existing tab navigation style
- Citation links: blue underlined text, distinct from regular text
- Mode indicator: use chip/badge component from design system
