# Specs: Contributor Documentation

---

## Behavioral Specifications

### Audience Hierarchy

| Audience | What They Need | Primary Docs |
|----------|---------------|-------------|
| New developer | Set up environment, understand patterns, start coding | QUICKSTART.md, DEVELOPMENT.md |
| Backend developer | Add endpoints, modify RAG, debug services | API.md, ARCHITECTURE.md, DEVELOPMENT.md |
| Flutter developer | Build UI features, connect to API | ARCHITECTURE.md (Flutter section), DEVELOPMENT.md |
| Legal advisor | Understand what data exists, verify accuracy | LAW_CORPUS.md |
| Stakeholder | Understand capabilities and architecture | README.md, ARCHITECTURE.md |

### Documentation Standards

| Standard | Requirement |
|----------|------------|
| Language | English (primary), with Georgian terms for legal concepts |
| Code examples | Every concept must have a runnable example |
| Diagrams | Use Mermaid for all architecture/flow diagrams |
| Versioning | Docs include "last updated" date |
| Links | Cross-reference between docs, never duplicate content |
| Curl examples | Every API endpoint has a copy-pasteable curl command |
| Prerequisites | List exact versions (Python 3.11+, not just "Python") |

---

## Technical Constraints

### File Structure
```
docs/
  QUICKSTART.md          — Zero-to-running guide
  ARCHITECTURE.md        — System design and decisions
  API.md                 — Complete API reference
  DEVELOPMENT.md         — Contributing guide
  LAW_CORPUS.md          — Legal data documentation
  assets/                — Diagrams, screenshots
README.md                — Root overview (links to docs/)
```

### Content Rules
- **No orphan docs** — every doc is linked from at least one other doc
- **No stale content** — if something changes, the doc must reference a source of truth (code file, config file)
- **No implementation details in README** — keep README high-level, link to detailed docs
- **Test the docs** — every command/curl example must be verified to work
- **Prefer diagrams over text** for architecture and flow explanations
- **Include "gotchas"** sections — document known issues and workarounds

### Sensitive Content
- Do NOT document API keys, passwords, or secrets
- Reference `.env.example` for environment variables
- Do NOT include production server IPs or credentials
- Reference `.agents/context/production.md` for production details (which should also be sanitized)

### Cross-References
- `QUICKSTART.md` → links to ARCHITECTURE.md for deeper understanding
- `ARCHITECTURE.md` → links to API.md for endpoint details
- `API.md` → links to DEVELOPMENT.md for how to add new endpoints
- `DEVELOPMENT.md` → links to workflow files (`.agents/workflows/`)
- `LAW_CORPUS.md` → links to `law_corpus/` directory for implementation

### Quality Checks
- [ ] Every curl example returns the expected response
- [ ] Quick start guide tested on a clean environment
- [ ] All internal links resolve (no broken links)
- [ ] No reference to internal tools/scripts that don't exist
- [ ] Georgian terms include English translations in parentheses
