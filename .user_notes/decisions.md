# 🧭 Architecture & Product Decisions

> Record every meaningful decision with rationale. Future-you (and AI agents) will thank you.

---

## Template

```
### [Date] — Decision Title
**Context:** What led to this decision  
**Decision:** What was decided  
**Rationale:** Why this was the right call  
**Alternatives considered:** What else was on the table  
**Revisit when:** Conditions that would make us reconsider  
```

---

## Decisions

### 2026-05-04 — Use google-genai SDK (not google-cloud-aiplatform)
**Context:** Needed to choose Vertex AI client library  
**Decision:** Use `google-genai` with `vertexai=True` flag  
**Rationale:** Simpler API, supports both API key and ADC auth, forward-compatible  
**Alternatives considered:** `google-cloud-aiplatform` (deprecated patterns), `vertexai` SDK  
**Revisit when:** Google announces SDK consolidation  

### 2026-05-04 — ADC Auth for Production Docker
**Context:** Initial setup used API keys, but needed GCP billing credits  
**Decision:** Mount GCP SA key via Docker volume, use Application Default Credentials  
**Rationale:** Billing goes through GCP project credits, more secure than API keys  
**Alternatives considered:** API key in .env (works but doesn't use GCP credits properly)  
**Revisit when:** Workload Identity Federation becomes simpler for VPS deployments  

### 2026-05-04 — ChromaDB for Vector Store (not Vertex AI Vector Search)
**Context:** Need vector search for law corpus  
**Decision:** ChromaDB (local, SQLite-backed) for MVP  
**Rationale:** Zero cost, no network latency, 9,450 docs is tiny — works perfectly local  
**Alternatives considered:** Vertex AI Vector Search (managed, scalable but $200+/mo minimum)  
**Revisit when:** Corpus exceeds 100K chunks or need multi-region deployment  

---

<!-- Add new decisions above this line -->
