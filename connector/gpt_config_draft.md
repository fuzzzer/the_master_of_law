# Custom GPT and listing draft — NOT published

Draft for the owner. Nothing here is created or published. Publishing a GPT, listing it in the GPT
store, submitting a ChatGPT plugin or a Claude directory entry each needs the owner's yes.

## Custom GPT

- **Name:** Georgian Law Master — Fuzzzy Law (ქართული სამართლის მაესტრო)
- **Description (store card):** Georgian law answers grounded in the official text. Quotes the
  article and links matsne.gov.ge; says so when it finds nothing. Not legal advice.
  / ქართული კანონმდებლობა ოფიციალური ტექსტით: ციტატა, matsne.gov.ge ბმული, არა იურიდიული კონსულტაცია.
- **Instructions:** `instructions/custom_gpt.md` (the part between the lines).
- **Conversation starters:**
  1. სამსახურიდან გამათავისუფლეს. რა უფლებები მაქვს და რა ვადებია?
  2. რამდენი დღე მაქვს სასამართლოს გადაწყვეტილების გასაჩივრებისთვის?
  3. ქირის ხელშეკრულება ვადაზე ადრე როგორ შევწყვიტო კანონიერად?
  4. What does the Georgian Civil Code say about the limitation period for a loan?
- **Capabilities:** web browsing off (answers must come from the action), image generation off,
  code interpreter off.
- **Action:** import `<public base URL>/api/v1/connector/openapi.json`. Authentication per access
  mode (see `instructions/custom_gpt.md`).
- **Privacy policy URL:** needed before sharing; the app's policy (Fuzzy Core LLC) awaits lawyer
  sign-off and would need a line about connector requests (what is logged: IP or user id, the
  query text, time; nothing else).
- **Profile picture:** from the brand's logo set (logo department), not generated here.

## Note on custom GPTs

OpenAI's help centre (summary of https://help.openai.com/en/articles/9442513, not fetched in full)
says custom GPTs are being retired in favour of plugins, Enterprise workspaces first on
11 December 2026. The MCP server is the longer-lived path: in ChatGPT it is added as a custom MCP
server and can be submitted as a plugin, which needs a public HTTPS endpoint and OpenAI's review.

## ChatGPT plugin (custom MCP server) draft

- Name: Fuzzzy Law — Georgian law sources
- Description: Exact Georgian law texts with official matsne.gov.ge links and version dates, and
  real Supreme Court decisions. Read-only. Sources, not legal advice.
- URL: `<public base URL>/mcp`; authentication: none (open mode); OAuth sign-in is not built yet.

## Claude directory draft

Same name and description; URL `<public base URL>/mcp`; authless (OAuth sign-in not built yet).
