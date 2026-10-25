# Any other AI agent

Give the agent the system prompt in `system_prompt.txt` and one of these:

- **MCP** (any MCP client): Streamable HTTP at `<public base URL>/mcp`. Tools: `search_law`,
  `get_article`, `browse_code`, `find_court_practice`, `verify_citation`, `list_codes`, plus `search`
  and `fetch`.
- **Plain HTTP / OpenAPI tools**: import `<public base URL>/api/v1/connector/openapi.json`; operation
  ids `searchLaw`, `getArticle`, `browseCode`, `findCourtPractice`, `verifyCitation`, `listCodes`.
  (The prompt names the MCP tool names; an HTTP agent's tools are the operation ids. The meaning is
  the same.)
- **OpenAI Responses API**: `tools=[{"type": "mcp", "server_label": "fuzzzy_law", "server_url":
  "<public base URL>/mcp", "require_approval": "never"}]` — safe to skip approval because every
  tool is read-only.

Key mode: send `Authorization: Bearer <key>`.

Minimum behaviour to check before trusting an agent setup (the scorecard's "outside AI + connector"
run measures this, `eval/scorecard/run_external.sh`):

1. It calls a tool before answering a legal question.
2. Every article it relies on is quoted and linked.
3. A deadline missing from the stored text is reported as missing, not filled in.
4. With no court practice found, it does not mention court practice.
5. It refuses unlawful requests and suggests a lawyer when stakes are high.
