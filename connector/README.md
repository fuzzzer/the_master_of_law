# Fuzzzy Law connector — Georgian law sources for ChatGPT, Claude and other AI agents

The connector lets a person's own AI assistant answer Georgian law questions from real sources. It
returns exact law text with the official matsne.gov.ge link and version date, and real Supreme Court
decisions where the server has them. It never writes advice and never calls a model; the user's AI
writes the answer, guided by the custom instructions in `instructions/`.

| Piece | Where | For |
|---|---|---|
| MCP server "Fuzzzy Law — Georgian law sources" | `POST /mcp` (Streamable HTTP, stateless, JSON) | ChatGPT custom MCP server / plugin, Claude custom connector, Claude API MCP connector, OpenAI Responses `mcp` tool, any MCP client |
| REST mirror | `/api/v1/connector/*` | custom GPT Actions, plain HTTP agents |
| OpenAPI 3.1 for a GPT Action | `GET /api/v1/connector/openapi.json` (copy: `openapi.json`) | paste or import into the GPT editor |
| Custom instructions | `instructions/` | custom GPT, Claude Project, any agent |
| GPT setup draft (not published) | `gpt_config_draft.md` | the owner's later decision |

## Tools

All read-only (`readOnlyHint`), descriptions in English and Georgian.

| MCP tool | REST operation | Returns |
|---|---|---|
| `search_law(query, code?, limit)` | `GET /search` `searchLaw` | articles with an exact snippet, code, article number, link, version date; `found=false` when nothing matched |
| `get_article(code, article, paragraph?)` | `GET /articles` `getArticle` | full exact text, paragraphs, link, version date, previous and next article |
| `browse_code(code, chapter?, offset, limit)` | `GET /structure` `browseCode` | chapters, or article numbers and titles |
| `find_court_practice(query, limit)` | `GET /court-practice` `findCourtPractice` | decisions with case number, court, year/date, snippet, link if stored; `none_found` / `source_unavailable` said plainly |
| `verify_citation(code, article, claim, paragraph?)` | `POST /verify-citation` `verifyCitation` | exists? repealed? the actual text, and a word-and-number overlap check (labelled: not a legal judgement) |
| `list_codes()` | `GET /codes` `listCodes` | codes, article counts, links, version dates |
| `search(query)` / `fetch(id)` | — | the pair ChatGPT deep research and company knowledge expect: `{results:[{id,title,url}]}` and `{id,title,text,url,metadata}` |

Every result carries `source_url`, `version_date` / `in_force_since` (or a `version_note` saying the
date is not recorded, or that the stored text looks incomplete) and the not-legal-advice `notice`.
The connector reads the version columns a newer article store adds (`version_date` on codes,
`in_force_since` / `effective_date` / `version_date` on articles, `matsne_url`) and rebuilds the matsne
link from the document id when a row carries none.

## Run it locally

```bash
cd backend
# standalone: only the connector (needs the article store; Chroma for court practice)
CHROMA_PERSIST_DIR=<corpus>/chroma .venv/bin/uvicorn app.connector_main:app --port 8010
# or inside the main app
CONNECTOR_ENABLED=true .venv/bin/uvicorn app.main:app --port 8000
```

Check it: `curl 'localhost:8010/api/v1/connector/articles?code=civil_code&article=138'`, or with the MCP
Python SDK: `async with mcp.Client("http://localhost:8010/mcp") as c: await c.list_tools()`.

## Settings (environment)

| Variable | Default | Meaning |
|---|---|---|
| `CONNECTOR_ENABLED` | `false` | mount the connector in the main app; off = nothing changes |
| `CONNECTOR_ACCESS_MODE` | `open` | `open` (per-IP limit), `api_key`, `oauth` (per-user quotas) |
| `CONNECTOR_PUBLIC_BASE_URL` | `http://localhost:8000` | public origin; goes into the OpenAPI `servers` and OAuth metadata |
| `CONNECTOR_RATE_LIMIT_PER_MINUTE` | `30` | per caller |
| `CONNECTOR_DAILY_QUOTA` | `1000` | per signed-in user (a key entry may set its own) |
| `CONNECTOR_API_KEYS_FILE` | `connector_api_keys.json` | `{"<sha256 of key>": {"user": "...", "daily_quota": N}}` — hashes only |
| `CONNECTOR_OAUTH_ISSUER`, `CONNECTOR_OAUTH_AUDIENCE`, `CONNECTOR_OAUTH_JWKS_URL` | empty | the sign-in service whose tokens are accepted |
| `CONNECTOR_ALLOWED_HOSTS` | empty | Host values `/mcp` accepts (DNS-rebinding protection) |

Rate limits use the app's Redis sliding window (fails open outside production, closed in production).
Behind a reverse proxy, run uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy>` so the
per-IP limit sees the caller's address, not the proxy's.

Make an API key (the key is shown once; only its hash is stored):

```bash
python3 -c "import secrets,hashlib,json;k='fzl_'+secrets.token_urlsafe(24);print(k);print(json.dumps({hashlib.sha256(k.encode()).hexdigest():{'user':'NAME','daily_quota':1000}}))"
```

## Sign-in modes

- `api_key`: callers send `Authorization: Bearer <key>`. Works for a GPT Action (Authentication →
  API Key → Bearer) and the Claude API MCP connector (`authorization_token`). ChatGPT's and Claude's
  connector screens do not take a static key; they use OAuth or no sign-in.
- `oauth`: the connector is an OAuth resource server. It accepts RS256/ES256 JWTs from
  `CONNECTOR_OAUTH_ISSUER` (keys from `CONNECTOR_OAUTH_JWKS_URL`), answers 401 with a
  `WWW-Authenticate` pointing at `/.well-known/oauth-protected-resource`, and publishes that metadata
  so ChatGPT and Claude find the sign-in service. The sign-in service itself (one that supports
  dynamic client registration or client ID metadata documents, as both clients require) is not part
  of this code and is an owner decision.

## Tests

`backend/tests/test_law_connector_service.py`, `test_connector_mcp.py`, `test_connector_rest.py`,
`test_connector_access.py`, `test_external_ai_target.py`.
