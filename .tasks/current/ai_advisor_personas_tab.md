# Task: AI Advisor Personas — Smart Legal Chat Tab

> **Goal:** Add a new "Advisor" tab to the bottom navigation that provides persona-based AI legal consultation. Each persona is a specialized legal agent (Criminal, Financial, Family, etc.) with tailored system prompts, response formatting, and RAG source weighting. Users can also chat without a persona for general legal help.

---

## Why This Feature Matters

The core mission is **making law accessible**. A generic "chat with AI" is not enough — most citizens don't even know *what kind* of legal help they need. Personas solve this by:

1. **Reducing cognitive load** — "I need a financial advisor" is easier than "I need to ask about tax code article 309"
2. **Delivering domain-formatted responses** — A criminal advisor structures answers around charges/defenses/rights. A financial advisor structures around obligations/deadlines/penalties.
3. **Optimizing RAG retrieval** — Each persona can weight certain ChromaDB collections and legal codes higher
4. **Building trust** — Specialized agents feel more competent than a generic chatbot

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                 Flutter App                      │
│                                                  │
│  ┌───────────────────────────────────────────┐   │
│  │  New Tab: "მრჩეველი" (Advisor)            │   │
│  │                                           │   │
│  │  ┌─────────────────────────────────┐      │   │
│  │  │  Persona Selector (horizontal)  │      │   │
│  │  │  [🔓Criminal][💰Financial]...   │      │   │
│  │  └─────────────────────────────────┘      │   │
│  │  ┌─────────────────────────────────┐      │   │
│  │  │  Chat Area (persona-styled)     │      │   │
│  │  │  AI responses formatted per     │      │   │
│  │  │  persona's domain structure     │      │   │
│  │  └─────────────────────────────────┘      │   │
│  │  ┌─────────────────────────────────┐      │   │
│  │  │  Input + RAG toggles + Send     │      │   │
│  │  └─────────────────────────────────┘      │   │
│  └───────────────────────────────────────────┘   │
│                                                  │
│  Bottom Nav: Chat | Cases ⭐ | Advisor | Laws | Profile │
└──────────────────────┬──────────────────────────┘
                       │ HTTPS / WebSocket
                       ▼
┌─────────────────────────────────────────────────┐
│                 FastAPI Backend                   │
│                                                  │
│  POST /api/v1/advisor/chat/{id}/send             │
│    ├── persona_id → PersonaPromptRegistry        │
│    ├── rag_config (auto-tuned per persona)        │
│    └── Gemini 3.1 Pro + persona system prompt     │
│                                                  │
│  GET  /api/v1/advisor/personas                   │
│    └── Returns all available personas + metadata  │
│                                                  │
│  Existing RAG Pipeline (5-stage, multi-collection)│
│    └── Weighted by persona preferences            │
└─────────────────────────────────────────────────┘
```

---

## Part 1: Backend — Persona Agent System

### 1.1 Persona Data Model

**File:** `backend/app/models/persona.py`

```python
# No DB table needed initially — personas are config-driven
# Store in app/config/personas.py as frozen dataclasses

@dataclass(frozen=True)
class AdvisorPersona:
    id: str                          # "criminal", "financial", "family", etc.
    name_ka: str                     # Georgian display name
    name_en: str                     # English fallback
    icon: str                        # Emoji or icon key
    description_ka: str              # What this advisor does (Georgian)
    description_en: str              # English fallback
    color_hex: str                   # Accent color for UI theming
    system_prompt: str               # Full system prompt for Gemini
    rag_config: RAGCollectionConfig  # Default source weighting
    response_sections: list[str]     # Expected sections in response
    legal_domains: list[str]         # Which legal domains this covers
    temperature: float = 0.1        # Gemini temperature
    max_output_tokens: int = 8192
```

### 1.2 Persona Definitions

**File:** `backend/app/config/personas.py`

Define these personas (at minimum):

| ID | Name (KA) | Name (EN) | Icon | RAG Bias | Key Domains |
|----|-----------|-----------|------|----------|-------------|
| `general` | ზოგადი მრჩეველი | General Advisor | ⚖️ | All equal | All |
| `criminal` | სისხლის სამართლის მრჩეველი | Criminal Advisor | 🔓 | court_practice ↑, grand_chamber ↑ | Criminal |
| `financial` | ფინანსური მრჩეველი | Financial Advisor | 💰 | legal_codes ↑ (tax, business) | Tax, Business |
| `family` | საოჯახო მრჩეველი | Family Law Advisor | 👨‍👩‍👧 | legal_codes ↑ (civil) | Family, Civil |
| `labor` | შრომის მრჩეველი | Labor Law Advisor | 👷 | legal_codes ↑ (labor code) | Labor |
| `property` | ქონებრივი მრჩეველი | Property Advisor | 🏠 | legal_codes ↑ (civil, property) | Property, Civil |

#### Persona System Prompt Pattern

Each persona extends the base `LEGAL_ANALYSIS_SYSTEM` prompt with domain-specific instructions:

```python
CRIMINAL_ADVISOR_PROMPT = (
    BASE_LEGAL_ANALYSIS +
    "\n\nSPECIALIZATION: CRIMINAL LAW\n"
    "You are a criminal defense specialist. Structure EVERY response as:\n"
    "1. 🚨 ბრალდების ანალიზი (Charge Analysis) — what they're accused of\n"
    "2. 🛡️ დაცვის საშუალებები (Defense Options) — every possible defense\n"
    "3. 📋 ბრალდებულის უფლებები (Rights of the Accused) — constitutional + procedural\n"
    "4. ⏰ ვადები და პროცედურები (Deadlines & Procedures) — what to do NOW\n"
    "5. 🤝 პლეა ბარგეინი (Plea Bargain) — when applicable\n"
    "6. ⚠️ რისკის შეფასება (Risk Assessment) — realistic outcome scenarios\n"
    "ALWAYS prioritize: immediate rights, procedural violations, statute of limitations.\n"
    "Cite სისხლის სამართლის კოდექსი AND სისხლის სამართლის საპროცესო კოდექსი.\n"
)

FINANCIAL_ADVISOR_PROMPT = (
    BASE_LEGAL_ANALYSIS +
    "\n\nSPECIALIZATION: FINANCIAL & TAX LAW\n"
    "You are a financial law specialist. Structure EVERY response as:\n"
    "1. 💰 ფინანსური ვალდებულებები (Financial Obligations) — what's owed, to whom\n"
    "2. 📊 საგადასახადო ანალიზი (Tax Analysis) — applicable tax rules\n"
    "3. 📋 ვადები (Deadlines) — filing dates, payment schedules\n"
    "4. 🛡️ შეღავათები და გამონაკლისები (Benefits & Exemptions) — tax breaks\n"
    "5. ⚠️ ჯარიმები და სანქციები (Penalties & Sanctions) — what happens if...\n"
    "6. 📝 რეკომენდაციები (Recommendations) — concrete next steps\n"
    "Use precise monetary calculations when possible.\n"
    "Cite საგადასახადო კოდექსი, სამოქალაქო კოდექსი as applicable.\n"
)
# ... similar for family, labor, property
```

### 1.3 New API Endpoints

**File:** `backend/app/routes/advisor_router.py`

| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/advisor/personas` | 0 | List all available personas with metadata |
| POST | `/api/v1/advisor/chat/{id}/send` | **1** | Send message with persona context |
| WS | `/api/v1/advisor/chat/{id}/ws` | 1 | WebSocket streaming with persona |

**Key difference from existing chat:** The `send` endpoint accepts `persona_id` and auto-applies:
- The persona's system prompt (replaces default `LEGAL_ANALYSIS_SYSTEM`)
- The persona's default `rag_config` (user can still override)
- The persona's response temperature

```python
class AdvisorChatRequest(BaseModel):
    message: str
    persona_id: str = "general"       # Which advisor persona
    rag_config: RAGCollectionConfig | None = None  # Override persona default
```

**Response format** — same as existing `ChatSendResponse` but add:
```python
class AdvisorChatResponse(ChatSendResponse):
    persona_id: str                   # Which persona answered
    response_sections: list[str]      # Section headers found in response
```

### 1.4 Advisor Service

**File:** `backend/app/services/advisor_service.py`

```python
class AdvisorService:
    """Wraps existing legal analysis with persona-specific behavior."""

    def __init__(self, persona_registry, rag_service, analysis_service):
        self.personas = persona_registry
        self.rag = rag_service
        self.analysis = analysis_service

    async def chat(self, conversation_id, message, persona_id, rag_config_override=None):
        persona = self.personas.get(persona_id)

        # Use persona's RAG config, allow user override
        effective_rag = rag_config_override or persona.rag_config

        # Run existing 5-stage RAG pipeline
        chunks = await self.rag.retrieve(message, effective_rag)

        # Use persona's system prompt instead of default
        response = await self.analysis.analyze(
            message=message,
            context_chunks=chunks,
            system_prompt=persona.system_prompt,
            temperature=persona.temperature,
        )

        return AdvisorChatResponse(
            response=response,
            persona_id=persona_id,
            # ... existing fields
        )
```

### 1.5 Backend File Summary

| File | Action | Description |
|------|--------|-------------|
| `app/config/personas.py` | **NEW** | All persona definitions (dataclasses) |
| `app/schemas/advisor_schema.py` | **NEW** | Request/response schemas |
| `app/routes/advisor_router.py` | **NEW** | 3 endpoints (list, send, ws) |
| `app/services/advisor_service.py` | **NEW** | Persona-aware chat logic |
| `app/prompts/advisor_prompts.py` | **NEW** | Per-persona system prompts |
| `app/prompts/registry.py` | **MODIFY** | Register new persona prompts |
| `app/main.py` | **MODIFY** | Register advisor router |
| `app/services/legal_analysis_service.py` | **MODIFY** | Accept custom system_prompt param |

---

## Part 2: Flutter — Advisor Tab & UI

### 2.1 Navigation Update

**Current:** 5 tabs → Chat, Cases ⭐, Laws, Notes, Profile
**New:** 6 tabs → Chat, Cases ⭐, **Advisor**, Laws, Notes, Profile

Or alternatively, **replace the existing Chat tab** with the Advisor tab (since Advisor IS the advanced chat). Recommendation: **Add as a new tab** between Cases and Laws, making it 6 tabs total. The existing Chat tab stays for simple case-linked conversations; Advisor is the standalone expert consultation.

> **Decision needed:** Add 6th tab or replace existing Chat tab?

### 2.2 Feature Structure (feature-first architecture)

```
lib/src/features/advisor/
├── data/
│   ├── models/
│   │   ├── advisor_persona_model.dart      # Persona data model
│   │   ├── advisor_chat_request.dart       # Request with persona_id
│   │   └── advisor_chat_response.dart      # Response with sections
│   ├── repositories/
│   │   ├── advisor_repository.dart         # API calls
│   │   └── advisor_local_repository.dart   # Local preferences (last persona, history)
│   └── datasources/
│       └── advisor_api_datasource.dart     # HTTP/WS client
├── domain/
│   ├── entities/
│   │   └── advisor_persona.dart            # Domain entity
│   └── usecases/
│       ├── get_personas.dart
│       ├── send_advisor_message.dart
│       └── switch_persona.dart
├── presentation/
│   ├── cubit/
│   │   ├── advisor_cubit.dart              # Main state management
│   │   ├── advisor_state.dart              # States
│   │   └── persona_selector_cubit.dart     # Persona selection state
│   ├── pages/
│   │   ├── advisor_page.dart               # Main advisor screen
│   │   └── persona_detail_page.dart        # Full persona info
│   └── widgets/
│       ├── persona_selector.dart           # Horizontal scrollable cards
│       ├── persona_card.dart               # Individual persona card
│       ├── advisor_chat_area.dart          # Chat messages area
│       ├── advisor_message_bubble.dart     # Persona-styled AI bubble
│       ├── advisor_input_bar.dart          # Input with persona context
│       ├── section_collapse_card.dart      # Collapsible response sections
│       └── advisor_empty_state.dart        # Welcome/persona picker
└── advisor.dart                            # Feature barrel export
```

### 2.3 Persona Selector UI

The top of the Advisor screen shows a horizontally scrollable list of persona cards:

```
┌──────────────────────────────────────────┐
│  Persona Selector (horizontal scroll)     │
│                                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │  ⚖️     │ │  🔓     │ │  💰     │    │
│  │ ზოგადი  │ │სისხლის  │ │ფინანსუ-│    │
│  │მრჩეველი │ │სამართლის│ │  რი     │    │
│  │         │ │         │ │         │    │
│  │ General │ │Criminal │ │Financial│    │
│  └─────────┘ └─────────┘ └─────────┘    │
│                                          │
│  ← swipe for more →                     │
└──────────────────────────────────────────┘
```

**Design specs:**
- Cards have the persona's `color_hex` as accent (subtle gradient or left border)
- Selected card: elevated, accent border, scaled slightly (1.02)
- Unselected: muted, no elevation
- Each card: icon (large), name (Georgian), subtitle (English)
- Tapping a card switches persona mid-conversation (with confirmation if messages exist)
- "No persona" option = first card (General Advisor)

### 2.4 Chat Area — Persona-Styled Messages

AI response bubbles change styling based on active persona:

- **Left border color** matches persona's `color_hex`
- **Header badge** shows persona icon + name (e.g., "🔓 სისხლის სამართლის მრჩეველი")
- **Response sections** are collapsible cards (parsed from the structured response)
- Each section has the emoji header from the persona's template

```
┌─ AI Response (Criminal Advisor) ────────────┐
│ 🔓 სისხლის სამართლის მრჩეველი               │
│                                              │
│ ▼ 🚨 ბრალდების ანალიზი                      │
│   [Expanded section content...]              │
│                                              │
│ ▶ 🛡️ დაცვის საშუალებები                     │
│   [Collapsed — tap to expand]                │
│                                              │
│ ▶ 📋 ბრალდებულის უფლებები                   │
│ ▶ ⏰ ვადები და პროცედურები                    │
│ ▶ ⚠️ რისკის შეფასება                         │
│                                              │
│ Sources: 📜 Laws (8) | ⚖️ Court (5)         │
│                                    [Copy] 📋│
└──────────────────────────────────────────────┘
```

### 2.5 Input Bar

Same as existing chat input but with persona context indicator:

```
┌──────────────────────────────────────────┐
│ 🔓 Criminal  │ აღწერეთ...    │ [⚙] [➤] │
│              │               │          │
└──────────────────────────────────────────┘
```

- Left: active persona chip (tappable to switch)
- Center: text input with persona-specific placeholder
- Right: RAG settings gear icon + send button
- RAG toggles: same as existing feature flag chips, but persona sets defaults

### 2.6 Empty State / Welcome Screen

When no conversation is active, show a persona-aware welcome:

```
┌──────────────────────────────────────────┐
│                                          │
│         ⚖️                               │
│   აირჩიეთ მრჩეველი                       │
│   Choose Your Advisor                    │
│                                          │
│   ┌─────────┐  ┌─────────┐              │
│   │ 🔓      │  │ 💰      │              │
│   │Criminal │  │Financial│              │
│   │         │  │         │              │
│   └─────────┘  └─────────┘              │
│   ┌─────────┐  ┌─────────┐              │
│   │ 👨‍👩‍👧     │  │ 👷      │              │
│   │ Family  │  │ Labor   │              │
│   └─────────┘  └─────────┘              │
│                                          │
│   ან დაიწყეთ ზოგადი კონსულტაცია          │
│   [  ⚖️ ზოგადი მრჩეველი  ]              │
│                                          │
└──────────────────────────────────────────┘
```

### 2.7 State Management (Cubit)

```dart
// advisor_state.dart
class AdvisorState {
  final List<AdvisorPersona> personas;        // Available personas
  final AdvisorPersona? activePersona;        // Currently selected
  final List<ChatMessage> messages;           // Conversation messages
  final RagConfigModel ragConfig;             // Active RAG config
  final String? conversationId;               // Backend conversation ID
  final AdvisorStatus status;                 // idle, loading, streaming, error
  final String? errorMessage;
}

enum AdvisorStatus { idle, loadingPersonas, ready, sending, streaming, error }
```

---

## Part 3: Advanced Features

### 3.1 Persona Memory (Per-Conversation)

Each advisor conversation remembers which persona was used. When resuming a conversation, the same persona is auto-selected.

```python
# Backend: add persona_id to conversation model
class Conversation:
    # ... existing fields
    persona_id: str | None = None  # NEW — which persona was used
```

### 3.2 Persona Switching Mid-Conversation

User can switch personas mid-conversation. When this happens:
- Show a system message: "🔄 მრჩეველი შეიცვალა → 💰 ფინანსური მრჩეველი"
- Next AI response uses the new persona's system prompt
- Previous context is preserved (conversation history stays)

### 3.3 Smart Persona Suggestion

After the user's first message (if no persona selected), the AI classifies the domain and suggests the best persona:

```
User: "დამსაქმებელმა სამსახურიდან გამათავისუფლა"

System: 💡 რეკომენდაცია: 👷 შრომის მრჩეველი
        ეს საკითხი შრომის სამართალს ეხება.
        [გამოიყენე შრომის მრჩეველი] [გააგრძელე ზოგადით]
```

This uses the existing `LegalClassifier` service to detect the domain.

### 3.4 Conversation History per Persona

The Advisor tab should show recent conversations grouped by persona:

```
Recent Consultations:
🔓 Criminal — "თავდასხმის ბრალდება" (2 days ago)
💰 Financial — "საგადასახადო დავალიანება" (5 days ago)
⚖️ General — "მეზობელთან დავა" (1 week ago)
```

### 3.5 Response Section Parsing

AI responses are structured by persona. The Flutter app should parse section headers and render them as collapsible cards:

```dart
List<ResponseSection> parseSections(String rawResponse) {
  // Split by emoji-prefixed headers like "🚨 ბრალდების ანალიზი"
  // Each section becomes a collapsible card
  final regex = RegExp(r'^(\p{Emoji}+)\s+(.+)$', multiLine: true, unicode: true);
  // ... parse into structured sections
}
```

---

## Part 4: Testing Checklist

### Backend Tests
- [ ] `GET /api/v1/advisor/personas` returns all personas with correct metadata
- [ ] `POST /advisor/chat/{id}/send` with `persona_id=criminal` uses criminal system prompt
- [ ] `POST /advisor/chat/{id}/send` with no persona defaults to "general"
- [ ] Persona's default `rag_config` is applied when user doesn't override
- [ ] User can override persona's `rag_config` per-message
- [ ] Conversation stores `persona_id` for session persistence
- [ ] WebSocket streaming works with persona context
- [ ] Smart persona suggestion returns correct domain classification

### Flutter Tests
- [ ] Persona selector renders all personas from API
- [ ] Tapping persona updates active persona in state
- [ ] Chat messages use persona-styled bubbles
- [ ] Response sections are parsed and rendered as collapsible cards
- [ ] RAG toggles reflect persona defaults but allow override
- [ ] Conversation history shows per-persona grouping
- [ ] Persona switching mid-conversation shows system message
- [ ] Empty state shows persona grid correctly
- [ ] Bottom navigation shows Advisor tab with correct icon
- [ ] Persona preference persists locally (Hive/SharedPreferences)

---

## Part 5: Implementation Order

| Step | Component | Est. Time | Dependencies |
|------|-----------|-----------|--------------|
| 1 | `app/config/personas.py` — Define all personas | 2h | None |
| 2 | `app/prompts/advisor_prompts.py` — Per-persona prompts | 2h | Step 1 |
| 3 | `app/schemas/advisor_schema.py` — Request/response | 1h | Step 1 |
| 4 | `app/services/advisor_service.py` — Persona-aware chat | 2h | Steps 1-3 |
| 5 | `app/routes/advisor_router.py` — 3 endpoints | 2h | Step 4 |
| 6 | Backend tests | 2h | Steps 1-5 |
| 7 | Flutter: `advisor_persona_model.dart` | 1h | Step 3 |
| 8 | Flutter: `advisor_repository.dart` | 1h | Steps 5, 7 |
| 9 | Flutter: `advisor_cubit.dart` + state | 2h | Steps 7, 8 |
| 10 | Flutter: Persona selector widget | 2h | Step 9 |
| 11 | Flutter: Chat area + styled bubbles | 3h | Step 9 |
| 12 | Flutter: Section parser + collapse cards | 2h | Step 11 |
| 13 | Flutter: Input bar with persona context | 1h | Step 10 |
| 14 | Flutter: Bottom nav update (add Advisor tab) | 1h | Step 13 |
| 15 | Flutter: Empty state + welcome screen | 1h | Step 10 |
| 16 | Flutter tests | 2h | Steps 7-15 |
| 17 | Smart persona suggestion (classifier integration) | 2h | Steps 4, 9 |
| 18 | Conversation history per persona | 2h | Steps 5, 9 |

**Total estimate:** ~30 hours (4 working days)

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tab placement | New 6th tab (not replacing Chat) | Chat stays for case-linked conversations; Advisor is standalone expert consultation |
| Persona storage | Config-driven (no DB) for v1 | Personas are static; DB later if user-customizable |
| Prompt architecture | Extends base `LEGAL_ANALYSIS_SYSTEM` | Reuse existing proven prompt; add specialization on top |
| RAG per persona | Default config + user override | Personas optimize defaults but user stays in control |
| Response parsing | Emoji header regex | Consistent with existing response structure pattern |

---

## Architecture Notes

- **Personas are agents** — each has its own system prompt, domain expertise, and response structure
- **Reuses entire existing RAG pipeline** — no new retrieval logic, just persona-aware prompting
- **Backward compatible** — existing Chat tab and endpoints untouched
- **`general` persona = existing behavior** — same as current `LEGAL_ANALYSIS_SYSTEM`
- **Credit cost: same as regular chat** (1 credit per message) — personas don't cost more
- **Georgian-first** — all persona names, descriptions, placeholders in Georgian
