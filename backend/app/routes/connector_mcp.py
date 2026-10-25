"""
Law connector MCP server — "Fuzzzy Law — Georgian law sources".

A remote MCP server (Streamable HTTP at /mcp) that ChatGPT, Claude and other
agents add as a connector. Every tool is read-only and returns sources only:
exact law text, its official matsne.gov.ge link and version date. The user's
own AI writes the answer. Tools are thin: the logic is in
``LawConnectorService``, shared with the REST mirror.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp_types import ToolAnnotations
from pydantic import Field
from starlette.applications import Starlette

from app.config.settings import settings
from app.middleware.connector_access_middleware import ConnectorAccessMiddleware
from app.routes import connector_router
from app.schemas.connector_schema import (
    CodeList,
    CodeStructure,
    CourtPracticeResult,
    FetchResult,
    GetArticleResult,
    SearchLawResult,
    SearchResults,
    VerifyCitationResult,
)
from app.services.law_connector_service import LawConnectorService, get_law_connector_service

SERVER_NAME = "fuzzzy-law"
SERVER_TITLE = "Fuzzzy Law — Georgian law sources"
SERVER_INSTRUCTIONS = """\
Georgian law sources (საქართველოს კანონმდებლობის წყაროები) from Fuzzzy Law.
The tools return exact text of Georgian codes with official matsne.gov.ge links
and version dates, and real Supreme Court decisions where available. They do
not give advice. When you answer from them:
- answer only from tool results; quote the article text and give its link;
- if nothing was found, say so; never invent articles, paragraphs or case numbers;
- check every deadline, amount and age with get_article before stating it;
- check a citation with verify_citation when unsure; flag uncertainty;
- say the text may have changed since its version date; suggest a lawyer when
  stakes are high; refuse help with breaking the law.
Answer in the user's language (Georgian by default)."""

READ_ONLY = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
)

# Tool descriptions, English then Georgian: the caller's AI reads them to
# decide when to call a tool, and users see them when adding the connector.
TOOL_DESCRIPTIONS = {
    "list_codes": (
        "List the Georgian codes available, with article counts, official links and "
        "version dates. ხელმისაწვდომი კოდექსების სია: მუხლების რაოდენობა, ოფიციალური "
        "ბმული და ვერსიის თარიღი."
    ),
    "search_law": (
        "Search Georgian law articles. Returns matching articles with an exact text snippet, "
        "code, article number, official matsne.gov.ge link and version date. found=false "
        "means nothing matched: say so, never guess. კანონის მუხლების ძიება: ზუსტი "
        "ამონარიდი, კოდექსი, მუხლის ნომერი, ოფიციალური ბმული და თარიღი."
    ),
    "get_article": (
        "Get the full exact text of one article, with its paragraphs, official link, "
        "version date and the previous and next article. Use it to check deadlines, "
        "amounts and ages before stating them. ერთი მუხლის სრული ზუსტი ტექსტი, "
        "პუნქტები, ოფიციალური ბმული, ვერსიის თარიღი და მეზობელი მუხლები."
    ),
    "browse_code": (
        "Show a code's structure: its chapters, or the article numbers and titles of one "
        "chapter. კოდექსის სტრუქტურა: თავები ან ერთი თავის მუხლების ნომრები და სათაურები."
    ),
    "find_court_practice": (
        "Find real Georgian Supreme Court decisions on an issue: case number, court, date, "
        "exact snippet and link when stored. status none_found or source_unavailable means "
        "you must not mention court practice. სასამართლო პრაქტიკა: რეალური "
        "გადაწყვეტილებები, საქმის ნომერი, თარიღი."
    ),
    "verify_citation": (
        "Check a citation: does the article (and paragraph) exist, is it repealed, and what "
        "does it actually say. Includes a word-and-number overlap check, not a legal "
        "judgement. ციტატის შემოწმება: არსებობს თუ არა მუხლი და რას ამბობს სინამდვილეში."
    ),
    "search": (
        "Search Georgian law articles and court decisions. Returns ids, titles and official "
        "links; call fetch with an id for the full text. კანონებისა და გადაწყვეტილებების "
        "ძიება."
    ),
    "fetch": (
        "Fetch the full text, official link and version details behind a search result id. "
        "ძიების შედეგის სრული ტექსტი და ოფიციალური ბმული."
    ),
}

CodeArg = Annotated[str, Field(description=(
    "Code id from list_codes (e.g. civil_code, labour_code) or its Georgian name "
    "(e.g. შრომის კოდექსი)."
))]
ArticleArg = Annotated[str, Field(description="Article number, e.g. 369, 48 or 166¹.")]
QueryArg = Annotated[str, Field(description=(
    "What to look for, best in Georgian legal terms, e.g. 'სააპელაციო საჩივრის ვადა'."
))]
OptionalCode = Annotated[str | None, Field(description="Optional: limit to one code (id or name).")]
OptionalParagraph = Annotated[str | None, Field(description="Optional paragraph number, e.g. 1.")]
OptionalChapter = Annotated[str | None, Field(description="Optional chapter to list articles of.")]


def build_connector_mcp_server(service: LawConnectorService | None = None) -> MCPServer:
    """A fresh MCP server instance (one per app: its session manager runs once)."""
    mcp = MCPServer(
        name=SERVER_NAME,
        title=SERVER_TITLE,
        description="Exact Georgian law texts with official links, for grounded answers.",
        instructions=SERVER_INSTRUCTIONS,
        website_url="https://matsne.gov.ge",
    )

    def svc() -> LawConnectorService:
        return service or get_law_connector_service()

    def tool(name: str):
        return mcp.tool(name=name, description=TOOL_DESCRIPTIONS[name], annotations=READ_ONLY)

    @tool("list_codes")
    def list_codes() -> CodeList:
        return svc().list_codes()

    @tool("search_law")
    def search_law(
        query: QueryArg,
        code: OptionalCode = None,
        limit: Annotated[int, Field(ge=1, le=25, description="How many articles.")] = 8,
    ) -> SearchLawResult:
        return svc().search_law(query, code, limit)

    @tool("get_article")
    def get_article(
        code: CodeArg, article: ArticleArg, paragraph: OptionalParagraph = None
    ) -> GetArticleResult:
        return svc().get_article(code, article, paragraph)

    @tool("browse_code")
    def browse_code(
        code: CodeArg,
        chapter: OptionalChapter = None,
        offset: Annotated[int, Field(ge=0, description="Skip this many articles.")] = 0,
        limit: Annotated[int, Field(ge=1, le=300, description="Articles per page.")] = 200,
    ) -> CodeStructure:
        return svc().browse_code(code, chapter, offset, limit)

    @tool("find_court_practice")
    def find_court_practice(
        query: QueryArg,
        limit: Annotated[int, Field(ge=1, le=10, description="How many decisions.")] = 5,
    ) -> CourtPracticeResult:
        return svc().find_court_practice(query, limit)

    @tool("verify_citation")
    def verify_citation(
        code: CodeArg,
        article: ArticleArg,
        claim: Annotated[str, Field(description="What your answer says this article provides.")],
        paragraph: OptionalParagraph = None,
    ) -> VerifyCitationResult:
        return svc().verify_citation(code, article, claim, paragraph)

    @tool("search")
    def search(query: QueryArg) -> SearchResults:
        return svc().search(query)

    @tool("fetch")
    def fetch(
        id: Annotated[str, Field(description="An id from search, e.g. article:civil_code:138.")],
    ) -> FetchResult:
        result = svc().fetch(id)
        if result is None:
            raise ValueError(f"No document with id '{id}'. Use an id returned by search.")
        return result

    return mcp


def connector_mcp_app(mcp: MCPServer) -> Starlette:
    """The Streamable HTTP app serving ``mcp`` at /mcp (stateless, JSON responses)."""
    hosts = settings.connector_allowed_host_list
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=bool(hosts),
        allowed_hosts=hosts,
        allowed_origins=[f"https://{h}" for h in hosts],
    )
    return mcp.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=security,
    )


def install_law_connector(app: FastAPI) -> MCPServer:
    """Add the connector to ``app``: REST mirror, MCP endpoint and access control.

    The returned server's ``session_manager.run()`` must be entered in the
    app's lifespan; it is also kept on ``app.state.connector_mcp`` for that.
    """
    mcp = build_connector_mcp_server()
    app.include_router(connector_router.router)
    app.router.routes.extend(connector_mcp_app(mcp).routes)
    app.add_middleware(ConnectorAccessMiddleware)
    app.state.connector_mcp = mcp
    return mcp
