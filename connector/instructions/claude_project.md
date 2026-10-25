# Claude: connector plus Project instructions

## Add the connector (claude.ai or Claude Desktop; Pro, Max, Team, Enterprise)

1. Customize → Connectors → Add custom connector.
2. Name: `Fuzzzy Law — Georgian law sources`; URL: `<public base URL>/mcp`.
3. Open mode: nothing else. (Claude's connector screen takes no static key, so key mode works only
   through the Claude API below; account sign-in through OAuth is left for later.)
4. Team and Enterprise: an Owner adds it for the organisation, then each member connects.
5. In a chat, turn the connector on from the tools menu.

## Project instructions (Project → Instructions)

Paste the full text of `system_prompt.txt` (English then Georgian, about 4,200 characters). It names
the MCP tools exactly as Claude sees them: `search_law`, `get_article`, `browse_code`,
`find_court_practice`, `verify_citation`, `list_codes`.

Suggested first messages to test:

- „სამსახურიდან გამათავისუფლეს მიზეზის თქმის გარეშე. რა ვადაში შემიძლია მოვითხოვო წერილობითი დასაბუთება?“
  (expected: Labour Code art. 48 quoted, 30 days, matsne link)
- „სამოქალაქო საქმეზე გადაწყვეტილება გამოცხადდა. რამდენი დღე მაქვს სააპელაციო საჩივრისთვის?“
  (expected: art. 369 quoted; because the stored text lacks part 1, the answer must say the term is not
  in the stored text and point to matsne, not state "14 days" from memory)

## Claude API (developers)

```python
client.beta.messages.create(
    model="claude-opus-5-5", max_tokens=16000,
    betas=["mcp-client-2025-11-20"],
    system=open("connector/instructions/system_prompt.txt").read(),
    mcp_servers=[{"type": "url", "url": "<public base URL>/mcp", "name": "fuzzzy-law"}],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "fuzzzy-law"}],
    messages=[{"role": "user", "content": "..."}],
)
```

Add `"authorization_token": "<key or token>"` to the server entry in key mode.
