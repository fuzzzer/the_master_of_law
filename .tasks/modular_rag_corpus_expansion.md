# 🏛️ Task: Modular RAG Corpus Expansion

> **Goal:** Build a modular multi-collection RAG system where Legal Codes, Supreme Court Practice, and Grand Chamber decisions are separate searchable collections — individually toggleable per query from backend and frontend.

---

## Context Loading (READ THESE FIRST)

| Document | Path | What It Tells You |
|----------|------|-------------------|
| **Project overview** | `.agents/context/project_status.md` | Current state of everything |
| **Backend architecture** | `.agents/context/backend.md` | 25 endpoints, 10 services, RAG pipeline |
| **Law corpus** | `.agents/context/law_corpus.md` | Existing ChromaDB setup (9,450 chunks) |
| **ChromaDB client** | `backend/app/integrations/chroma_client.py` | Current single-collection client |
| **RAG service** | `backend/app/services/rag_retrieval_service.py` | 5-stage pipeline implementation |
| **RAG constants** | `backend/app/config/constants.py` | `RAG_*` tuning params |
| **Settings** | `backend/app/config/settings.py` | `chroma_persist_dir`, `chroma_collection_name` |
| **Font-aware PDF extractor** | `eval/test_cases/extract_pdf_georgian.py` | Converts HKolkhety-font PDFs to Georgian Unicode |
| **Embedding pipeline** | `law_corpus/` | Full scrape→parse→chunk→embed→index pipeline |

---

## Current State

### What We Have

```
law_corpus/data/chroma/          ← ChromaDB with 1 collection
  └── "georgian_laws"            ← 9,450 chunks, 15 legal codes
                                    768-dim vectors (gemini-embedding-001)
                                    Metadata: code_name, article_number, citation_text, source_url

eval/test_cases/raw/             ← 79 Supreme Court PDF bulletins (2023-2026)
eval/test_cases/processed_v2/    ← 443 extracted cases in clean Georgian Unicode
  ├── supreme_court/criminal/    ← 181 cases
  ├── supreme_court/civil/       ← 121 cases  
  └── supreme_court/administrative/ ← 141 cases
```

### What's Missing
1. **Grand Chamber (დიდი პალატა)** — NOT downloaded yet (binding court interpretations)
2. **Supreme Court 2022** — NOT downloaded (criminal, civil, admin)
3. **Civil 2023** — NOT downloaded
4. **No ChromaDB collections** for court practice data
5. **Backend is hardcoded** to single `georgian_laws` collection

---

## Architecture Target

```
ChromaDB (3 independent collections)
  ├── "georgian_laws"           ← 15 legal codes (EXISTING ✅)
  │     9,450 chunks, articles from Matsne
  │
  ├── "court_practice"          ← Supreme Court case rulings (NEW)
  │     ~600+ cases, segmented by reasoning/resolution
  │     Metadata: case_id, category (criminal/civil/admin), 
  │               year, court_level, verdict_type
  │
  └── "grand_chamber"           ← Grand Chamber binding decisions (NEW)
        ~50-100 decisions, norm interpretations
        Metadata: case_id, category, norm_interpreted,
                  binding_rule (the established interpretation)
```

### Modular Query Flow

```
User Query → Query Expansion
  │
  ├─► Vector Search: "georgian_laws"      ← if enabled
  ├─► Vector Search: "court_practice"     ← if enabled
  ├─► Vector Search: "grand_chamber"      ← if enabled
  │
  ▼ Merge & Deduplicate (tag source collection)
  ▼ Rerank (top-20 across all collections)
  ▼ Legal Analysis (Gemini sees law articles + court precedents + binding interpretations)
```

Each collection can be toggled ON/OFF per request. Default: all enabled.

---

## Implementation Steps

### Step 1: Grand Chamber — Download & Extract

The Grand Chamber's legal interpretations are **binding on ALL courts** (this is stated on their page). This is the highest-impact data source.

#### 1.1 Discover PDFs

Scrape these 4 pages for PDF links:
```
https://www.supremecourt.ge/decisions-grand-chamber/siskhlis-samartlis-saqmeebze-didi-palata
https://www.supremecourt.ge/decisions-grand-chamber/samoqalaqo-samartlis-saqmeebze-didi-palata
https://www.supremecourt.ge/decisions-grand-chamber/administratsiul-da-skhva-kategoriis-saqmeebze-didi-palata
https://www.supremecourt.ge/decisions-grand-chamber/didi-palatis-gadatsyvetilebebshi-gamoyenebul-normata-ganmartebebi
```

The last one ("ნორმათა განმარტებები") is the most valuable — it's a compiled list of which norms the Grand Chamber has interpreted and HOW. This is essentially a binding legal dictionary.

#### 1.2 Download PDFs

Save to: `eval/test_cases/raw/supreme_court/grand_chamber/`
Use the download pattern from `eval/test_cases/download_cases.py`.

#### 1.3 Extract with Font-Aware Tool

Use the existing `eval/test_cases/extract_pdf_georgian.py`:
```bash
python3 eval/test_cases/extract_pdf_georgian.py \
  --all \
  --output-dir eval/test_cases/processed_v2/supreme_court/grand_chamber/
```

This tool handles the HKolkhety font → Georgian Unicode conversion automatically.
It detects font per text span:
- `HKolkhety` / `HKolkhetyMtav` → AkadTrans → convert to Georgian
- `Times New Roman` → real English → keep as-is
- `Baltica TD` → Russian → keep as-is

Output: Individual `.txt` files per case, 99.4% Georgian Unicode.

#### 1.4 Also Download Missing SC PDFs

**Criminal 2022** (from `old.supremecourt.ge`):
```python
{
    "sisxli-01-03-2022": "http://old.supremecourt.ge/files/upload-file/pdf/2022w-sisxli-krebuli-1-3.pdf",
    "sisxli-04-06-2022": "http://old.supremecourt.ge/files/upload-file/pdf/2022w-sisxli-krebuli-4-6.pdf",
    "sisxli-07-09-2022": "http://old.supremecourt.ge/files/upload-file/pdf/2022w-sisxli-krebuli-7-9.pdf",
    "sisxli-10-12-2022": "http://old.supremecourt.ge/files/upload-file/pdf/2022w-sisxli-krebuli-10-12.pdf",
}
```

**Civil 2022** (from `old.supremecourt.ge`):
```python
# Pattern: http://old.supremecourt.ge/files/upload-file/pdf/2022w-samoqalaqo-krebuli{N}.pdf
# N = 1..12
```

**Civil 2023** (from `supremecourt.ge`):
```python
# Pattern: https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/samoq-{MM}-2023.pdf
# MM = 01..12
```

**Admin 2022** — discover URLs from:
`https://www.supremecourt.ge/decisions/administratsiuli-samartlis-saqmeebze`

---

### Step 2: Chunk Court Practice for Embedding

Each extracted case `.txt` file needs to be chunked for ChromaDB.

#### Chunking Strategy for Court Decisions

Court decisions have a different structure than legal articles. Use semantic chunking:

```
Case Text Structure:
  ├── აღწერილობითი ნაწილი (Descriptive — facts)
  ├── სამოტივაციო ნაწილი (Reasoning — WHY the court decided)
  └── სარეზოლუციო ნაწილი (Resolution — WHAT was decided)
```

**Chunk boundaries:** Split at numbered sections (1., 2., 3. etc.) within each part.
**Target chunk size:** 500-1000 words (same as existing law corpus).
**Overlap:** 50 words between chunks.

#### Metadata Per Chunk

```python
{
    "source": "court_practice",           # or "grand_chamber"
    "case_id": "903ap-23",                # from filename
    "category": "criminal",               # criminal/civil/administrative
    "year": 2024,                         # from case text
    "section": "reasoning",              # descriptive/reasoning/resolution
    "court": "supreme_court",             # or "grand_chamber"
    "chunk_index": 0,                     # sequential within case
}
```

For Grand Chamber specifically, also extract:
```python
{
    "norm_interpreted": "სსკ 19 (მცდელობა)",  # which norm was interpreted
    "binding_rule": "შემძენთან კონტაქტის გარეშე = მომზადება",  # the binding interpretation
}
```

#### Implementation

Create: `eval/test_cases/build_court_embeddings.py`

Use the **same embedding model** as the law corpus:
- Model: `gemini-embedding-001`
- Dimensions: 768
- Task type: `RETRIEVAL_DOCUMENT`

Reference the existing embedding pipeline in `law_corpus/src/law_corpus/embedder.py` for the exact API call pattern.

---

### Step 3: Create Separate ChromaDB Collections

Create **2 new collections** alongside the existing one:

```python
# New collections
client = chromadb.PersistentClient(path="law_corpus/data/chroma")

# Existing (don't touch)
# client.get_collection("georgian_laws")  # 9,450 chunks

# NEW
court_practice = client.get_or_create_collection(
    name="court_practice",
    metadata={"description": "Supreme Court case rulings 2022-2026"}
)

grand_chamber = client.get_or_create_collection(
    name="grand_chamber", 
    metadata={"description": "Grand Chamber binding decisions and norm interpretations"}
)
```

All 3 collections use the **same embedding model** (768-dim, gemini-embedding-001), so query embeddings are compatible across all of them.

---

### Step 4: Backend — Multi-Collection ChromaClient

#### 4.1 Update `backend/app/integrations/chroma_client.py`

The current client is hardcoded to a single collection. Refactor to support multiple:

```python
class ChromaClient:
    """Multi-collection ChromaDB client."""
    
    # Collection registry
    COLLECTIONS = {
        "georgian_laws": "Legal codes from Matsne (15 codes, 9,450 chunks)",
        "court_practice": "Supreme Court case rulings (2022-2026, ~600 cases)",
        "grand_chamber": "Grand Chamber binding decisions and norm interpretations",
    }
    
    def connect(self) -> None:
        """Connect and verify all available collections."""
        self._client = chromadb.PersistentClient(path=str(self._persist_dir))
        self._collections = {}
        for name in self.COLLECTIONS:
            try:
                self._collections[name] = self._client.get_collection(name)
                logger.info("chroma_collection_loaded", name=name, 
                           count=self._collections[name].count())
            except Exception:
                logger.warning("chroma_collection_missing", name=name)
    
    def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 50,
        collections: list[str] | None = None,  # NEW: specify which collections
        where: dict | None = None,
    ) -> list[dict]:
        """Search across specified collections (default: all available)."""
        target = collections or list(self._collections.keys())
        all_hits = []
        
        for col_name in target:
            if col_name not in self._collections:
                continue
            col = self._collections[col_name]
            results = col.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
                **({"where": where} if where else {})
            )
            # Tag each hit with its source collection
            for i, chunk_id in enumerate(results["ids"][0]):
                all_hits.append({
                    "chunk_id": chunk_id,
                    "content": results["documents"][0][i],
                    "metadata": {**results["metadatas"][0][i], "_collection": col_name},
                    "distance": results["distances"][0][i],
                })
        
        # Sort by distance (best matches first)
        all_hits.sort(key=lambda x: x["distance"])
        return all_hits[:top_k]
```

> **IMPORTANT:** Keep backward compatibility. If `collections` param is None, search all. The existing `georgian_laws` collection must keep working exactly as before.

#### 4.2 Update `backend/app/services/rag_retrieval_service.py`

Pass collection selection through the RAG pipeline. The existing 5-stage pipeline stays the same, just Stage 1 (vector search) and Stage 2 (full-text search) gain a `collections` parameter.

#### 4.3 Add Collection Config to API Schemas

```python
# In backend/app/schemas/
class RAGCollectionConfig(BaseModel):
    """Controls which RAG collections to search."""
    legal_codes: bool = True        # "georgian_laws"
    court_practice: bool = True     # "court_practice"  
    grand_chamber: bool = True      # "grand_chamber"

# Add to chat send request:
class ChatSendRequest(BaseModel):
    message: str
    rag_config: RAGCollectionConfig | None = None  # Optional, defaults to all
```

#### 4.4 Update API Endpoints

Add collection config to these endpoints:
- `POST /api/v1/chat/{id}/send` — pass `rag_config` 
- `WS /api/v1/chat/{id}/ws` — pass in initial WS message
- `POST /api/v1/case-files/build` — pass `rag_config`

Add a new endpoint:
- `GET /api/v1/rag/collections` — returns available collections with status/counts

```python
@router.get("/api/v1/rag/collections")
async def list_collections():
    """List available RAG collections and their status."""
    chroma = get_chroma_client()
    return {
        "collections": [
            {
                "id": name,
                "name_ka": ...,  # Georgian display name
                "description": desc,
                "available": name in chroma._collections,
                "chunk_count": chroma._collections[name].count() if name in chroma._collections else 0,
            }
            for name, desc in ChromaClient.COLLECTIONS.items()
        ]
    }
```

---

### Step 5: Frontend Integration (Flutter)

In the chat/case-builder UI, add a settings panel (or a simple toggle group) that lets users select which knowledge sources to include in their query.

```
┌─────────────────────────────────┐
│ 📚 ცოდნის წყაროები              │
│                                 │
│ ☑️ კანონმდებლობა (15 კოდექსი)   │ ← Legal Codes
│ ☑️ სასამართლო პრაქტიკა         │ ← Court Practice  
│ ☑️ დიდი პალატა (სავალდებულო)   │ ← Grand Chamber
└─────────────────────────────────┘
```

The Flutter app should:
1. Call `GET /api/v1/rag/collections` to get available collections
2. Show toggles with Georgian labels
3. Pass selection in `rag_config` field when sending chat/building cases
4. Store per-case preferences (so a criminal case auto-enables court_practice+grand_chamber)

Reference for Flutter architecture: `frontend/.agents/orchestrator.md`

---

## Data Flow Summary

```
1. Download PDFs (Grand Chamber + SC 2022 + Civil 2023)
      ↓
2. Extract with font-aware tool (extract_pdf_georgian.py)
      ↓  
3. Chunk case texts (500-1000 word chunks with metadata)
      ↓
4. Embed with gemini-embedding-001 (768-dim, RETRIEVAL_DOCUMENT)
      ↓
5. Store in ChromaDB collections ("court_practice", "grand_chamber")
      ↓
6. Backend multi-collection search (ChromaClient refactor)
      ↓
7. API with rag_config parameter
      ↓
8. Frontend collection toggles
```

---

## Key Technical Constraints

1. **Embedding model MUST be `gemini-embedding-001`** with 768 dimensions — must match existing corpus
2. **Task type:** `RETRIEVAL_DOCUMENT` for indexing, `RETRIEVAL_QUERY` for search
3. **ChromaDB path:** `law_corpus/data/chroma/` — all collections in same persistent client
4. **Gemini SDK:** Use `google-genai` only. NOT `google-cloud-aiplatform` or `vertexai`
5. **GCP Project:** `gen-lang-client-0225498420`, region `us-central1`
6. **Auth for embeddings:** Use `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` from `backend/.env`
7. **Georgian text:** Always UTF-8, Mkhedruli range U+10D0–U+10FF
8. **Backward compatibility:** Existing `georgian_laws` collection and all current endpoints MUST keep working unchanged

---

## Success Criteria

- [ ] Grand Chamber PDFs downloaded and extracted to clean Georgian text
- [ ] Supreme Court 2022 + Civil 2023 PDFs downloaded and extracted
- [ ] All court practice text chunked with proper metadata
- [ ] `court_practice` ChromaDB collection populated (~600+ cases)
- [ ] `grand_chamber` ChromaDB collection populated (~50-100 decisions)
- [ ] `ChromaClient` supports multi-collection search
- [ ] RAG pipeline queries all enabled collections and merges results
- [ ] `GET /api/v1/rag/collections` endpoint returns available collections
- [ ] `POST /api/v1/chat/{id}/send` accepts `rag_config` parameter
- [ ] Frontend shows collection toggles (can be a later PR)
- [ ] Existing tests pass without modification (backward compatible)
- [ ] Eval score improves from 3.47/5 baseline (re-run eval to verify)

---