# Task: RAG Collection Feature Flags — Flutter + Backend

> **Goal:** Let users control which knowledge sources (laws, court practice, Grand Chamber) the AI searches when answering questions. Default = all sources enabled.

---

## Context — What Already Exists

### Backend (✅ Already Implemented)

The backend already supports modular RAG collection selection:

| Component | File | Status |
|-----------|------|--------|
| `RAGCollectionConfig` schema | `backend/app/schemas/rag_schema.py` | ✅ Done |
| `GET /api/v1/rag/collections` | `backend/app/routes/rag_router.py` | ✅ Done |
| `POST /chat/{id}/send` accepts `rag_config` | `backend/app/routes/chat_router.py:77` | ✅ Done |
| WS `/chat/{id}/ws` accepts `rag_config` | `backend/app/routes/ws_chat_router.py:55-62` | ✅ Done |
| `ChromaClient.vector_search(collections=)` | `backend/app/integrations/chroma_client.py` | ✅ Done |
| Source-specific prompt injection | `backend/app/services/legal_analysis_service.py:26-50` | ✅ Done |
| `POST /case-files/build` accepts `rag_config` | `backend/app/routes/...` | ✅ Done |

### Backend API Contract

**Request (chat send):**
```json
{
  "message": "რა უფლებები მაქვს დამსაქმებლის წინაშე?",
  "rag_config": {
    "legal_codes": true,
    "court_practice": true,
    "grand_chamber": true
  }
}
```

**Response (rag/collections):**
```json
{
  "collections": [
    {
      "id": "georgian_laws",
      "name_ka": "საქართველოს კანონმდებლობა",
      "description": "12 Georgian legal codes from Matsne",
      "available": true,
      "chunk_count": 15338
    },
    {
      "id": "court_practice",
      "name_ka": "სასამართლო პრაქტიკა",
      "description": "Supreme Court case rulings (2022-2026)",
      "available": true,
      "chunk_count": 5197
    },
    {
      "id": "grand_chamber",
      "name_ka": "დიდი პალატა",
      "description": "Grand Chamber binding decisions",
      "available": true,
      "chunk_count": 177
    }
  ]
}
```

### ChromaDB Collections

| Collection | Chunks | Always On? |
|------------|--------|-----------|
| `georgian_laws` | 15,338 | Yes (fallback — never empty) |
| `court_practice` | 5,197 | Default on, toggleable |
| `grand_chamber` | 177 | Default on, toggleable |

---

## What Needs to Be Built

### 1. Flutter — RAG Config Model

**File:** `lib/features/chat/data/models/rag_config_model.dart`

```dart
/// Controls which RAG knowledge sources the AI searches.
/// Maps directly to backend RAGCollectionConfig.
class RagConfigModel {
  final bool legalCodes;      // georgian_laws — always at least this
  final bool courtPractice;   // court_practice
  final bool grandChamber;    // grand_chamber

  const RagConfigModel({
    this.legalCodes = true,
    this.courtPractice = true,
    this.grandChamber = true,
  });

  Map<String, dynamic> toJson() => {
    'legal_codes': legalCodes,
    'court_practice': courtPractice,
    'grand_chamber': grandChamber,
  };

  factory RagConfigModel.fromJson(Map<String, dynamic> json) => RagConfigModel(
    legalCodes: json['legal_codes'] ?? true,
    courtPractice: json['court_practice'] ?? true,
    grandChamber: json['grand_chamber'] ?? true,
  );

  /// Laws only mode — fastest, no court practice
  factory RagConfigModel.lawsOnly() => const RagConfigModel(
    legalCodes: true,
    courtPractice: false,
    grandChamber: false,
  );

  /// Full research mode — all sources (default)
  factory RagConfigModel.full() => const RagConfigModel();
}
```

### 2. Flutter — Collection Info Model

**File:** `lib/features/chat/data/models/collection_info_model.dart`

```dart
class CollectionInfoModel {
  final String id;
  final String nameKa;
  final String description;
  final bool available;
  final int chunkCount;

  // ... fromJson, UI icon/color helpers
}
```

### 3. Flutter — Chat Repository Update

Update the chat repository to include `rag_config` in the send message request body:

```dart
Future<ChatResponse> sendMessage({
  required String conversationId,
  required String message,
  RagConfigModel? ragConfig,  // NEW
}) async {
  final body = {
    'message': message,
    if (ragConfig != null) 'rag_config': ragConfig.toJson(),
  };
  // POST to /api/v1/chat/{conversationId}/send
}
```

### 4. Flutter — RAG Collections Repository

New repository to fetch available collections:

```dart
class RagCollectionsRepository {
  Future<List<CollectionInfoModel>> getCollections() async {
    // GET /api/v1/rag/collections
  }
}
```

### 5. Flutter — Chat Cubit/Bloc Update

Add `ragConfig` to the chat state and expose methods to toggle sources:

```dart
// In chat cubit state
class ChatState {
  final RagConfigModel ragConfig;  // NEW — defaults to RagConfigModel.full()
  // ... existing fields
}

// Methods
void toggleCourtPractice(bool enabled);
void toggleGrandChamber(bool enabled);
void setRagConfig(RagConfigModel config);
```

### 6. Flutter — Source Toggle UI Widget

Build a compact UI for toggling sources in the chat screen. Two approaches:

**Option A: Chat header chips (recommended)**
Small filter chips above the message input:
```
[ 📜 კანონები ✓ ] [ ⚖️ პრაქტიკა ✓ ] [ 🏛️ დიდი პალატა ✓ ]
```

**Option B: Bottom sheet settings**
Gear icon next to send button → opens bottom sheet with toggle switches.

**Design considerations:**
- Show collection name in Georgian (`name_ka` from API)
- Show chunk count as subtitle (e.g., "15,338 ჩანაწერი")
- Gray out unavailable collections
- `georgian_laws` toggle is always on (disabled, checked) — it's the minimum
- Use appropriate icons: 📜 laws, ⚖️ court, 🏛️ Grand Chamber
- Persist user preference locally (Hive/SharedPreferences)

### 7. Flutter — Response Source Indicators

When the AI response comes back, show which sources contributed:

```dart
// In the AI response bubble, show small badges:
// "წყაროები: 📜 კანონები (12) | ⚖️ პრაქტიკა (5) | 🏛️ დიდი პალატა (2)"
```

This data is already available in `retrieved_chunks[].metadata._collection`.

---

## Backend Changes Needed (Minor)

### 1. Add `_collection` to RetrievedChunk response

Currently `RetrievedChunk` in `chat_schema.py` doesn't include the `_collection` field. Add it so Flutter can show source indicators:

**File:** `backend/app/schemas/chat_schema.py`
```python
class RetrievedChunk(BaseModel):
    # ... existing fields
    collection: str = ""  # NEW — which collection this chunk came from
```

**File:** `backend/app/routes/chat_router.py` (line ~102)
```python
chunk_models.append(RetrievedChunk(
    # ... existing fields
    collection=meta.get("_collection", "georgian_laws"),  # NEW
))
```

### 2. Add source summary to ChatSendResponse

```python
class ChatSendResponse(BaseModel):
    # ... existing fields
    sources_used: dict[str, int] = {}  # NEW — {"georgian_laws": 12, "court_practice": 5}
```

---

## Testing Checklist

- [ ] `GET /api/v1/rag/collections` returns 3 collections with correct counts
- [ ] Chat with `rag_config: null` searches all collections (default behavior)
- [ ] Chat with `rag_config: {"legal_codes": true, "court_practice": false, "grand_chamber": false}` searches only laws
- [ ] Chat with all flags `false` falls back to `georgian_laws` only (enforced by backend)
- [ ] Flutter UI shows toggle chips and persists preferences
- [ ] AI response shows which sources contributed
- [ ] WebSocket chat also respects `rag_config`
- [ ] Case builder also respects `rag_config`

---

## Implementation Order

1. **Backend:** Add `collection` field to `RetrievedChunk` + `sources_used` to response (30 min)
2. **Flutter:** Create `RagConfigModel` + `CollectionInfoModel` (30 min)
3. **Flutter:** Update chat repository to pass `rag_config` (30 min)
4. **Flutter:** Add `ragConfig` to chat cubit state (30 min)
5. **Flutter:** Build source toggle chips widget (1-2 hrs)
6. **Flutter:** Build response source indicators (1 hr)
7. **Flutter:** Persist user preference with Hive (30 min)
8. **Tests:** Backend + Flutter unit tests (1 hr)

**Total estimate:** ~5-6 hours

---

## Key Files to Modify

### Backend
| File | Change |
|------|--------|
| `app/schemas/chat_schema.py` | Add `collection` to `RetrievedChunk`, `sources_used` to response |
| `app/routes/chat_router.py` | Populate `collection` and `sources_used` |

### Flutter
| File | Change |
|------|--------|
| `lib/features/chat/data/models/rag_config_model.dart` | **NEW** — RAG config model |
| `lib/features/chat/data/models/collection_info_model.dart` | **NEW** — Collection info model |
| `lib/features/chat/data/repositories/chat_repository.dart` | Add `ragConfig` param |
| `lib/features/chat/data/repositories/rag_collections_repository.dart` | **NEW** — fetch collections |
| `lib/features/chat/presentation/cubit/chat_cubit.dart` | Add `ragConfig` to state |
| `lib/features/chat/presentation/widgets/source_toggle_chips.dart` | **NEW** — toggle UI |
| `lib/features/chat/presentation/widgets/source_indicators.dart` | **NEW** — response badges |

---

## Architecture Notes

- **Default = all sources ON** — users get the best possible answer out of the box
- **Laws-only mode** is useful for quick statute lookups without court interpretation
- **Grand Chamber is special** — binding decisions override everything; highlight this in UI
- **Per-conversation persistence** — once set, rag_config should persist for that conversation
- **Global preference** — user's default preference saved locally, applied to new conversations
