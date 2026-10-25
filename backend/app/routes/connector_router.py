"""
Law connector REST mirror — the MCP tools as plain HTTP, for custom GPT Actions.

Same operations, same service, same responses as the MCP server. The
OpenAPI 3.1 document a GPT Action imports is served at
/api/v1/connector/openapi.json and contains only these operations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.openapi.utils import get_openapi

from app.config.settings import settings
from app.schemas.connector_schema import (
    CodeList,
    CodeStructure,
    CourtPracticeResult,
    GetArticleResult,
    SearchLawResult,
    VerifyCitationRequest,
    VerifyCitationResult,
)
from app.services.connector_access_service import protected_resource_metadata
from app.services.law_connector_service import get_law_connector_service

router = APIRouter(prefix="/api/v1/connector", tags=["law connector"])
discovery_router = APIRouter(tags=["law connector"])

OPENAPI_TITLE = "Fuzzzy Law — Georgian law sources"
OPENAPI_DESCRIPTION = (
    "Exact texts of Georgian codes with official matsne.gov.ge links and version dates, "
    "and real Supreme Court decisions where available. Sources only, not legal advice."
)

CodeQuery = Annotated[str, Query(
    description="Code id from listCodes (e.g. civil_code) or its Georgian name."
)]
ArticleQuery = Annotated[str, Query(description="Article number, e.g. 369 or 166¹.")]


@router.get("/codes", operation_id="listCodes", summary="List available Georgian codes")
async def list_codes() -> CodeList:
    """Codes with article counts, official links and version dates."""
    return get_law_connector_service().list_codes()


@router.get("/search", operation_id="searchLaw", summary="Search Georgian law articles")
async def search_law(
    query: Annotated[str, Query(
        min_length=1, description="What to look for, best in Georgian legal terms."
    )],
    code: Annotated[str | None, Query(description="Optional: limit to one code.")] = None,
    limit: Annotated[int, Query(ge=1, le=25, description="How many articles.")] = 8,
) -> SearchLawResult:
    """Matching articles with exact snippet, link and version date.

    found=false means nothing matched.
    """
    return get_law_connector_service().search_law(query, code, limit)


@router.get("/articles", operation_id="getArticle", summary="Get one article's full text")
async def get_article(
    code: CodeQuery,
    article: ArticleQuery,
    paragraph: Annotated[str | None, Query(description="Optional paragraph number.")] = None,
) -> GetArticleResult:
    """Full exact text, paragraphs, link, version date and neighbouring articles.

    Use it to check deadlines.
    """
    return get_law_connector_service().get_article(code, article, paragraph)


@router.get("/structure", operation_id="browseCode", summary="Show a code's chapters or articles")
async def browse_code(
    code: CodeQuery,
    chapter: Annotated[str | None, Query(description="Optional chapter to list.")] = None,
    offset: Annotated[int, Query(ge=0, description="Paging offset.")] = 0,
    limit: Annotated[int, Query(ge=1, le=300, description="Articles per page.")] = 200,
) -> CodeStructure:
    """Chapters of a code, or article numbers and titles."""
    return get_law_connector_service().browse_code(code, chapter, offset, limit)


@router.get(
    "/court-practice", operation_id="findCourtPractice", summary="Find real court decisions"
)
async def find_court_practice(
    query: Annotated[str, Query(min_length=1, description="Legal issue in Georgian.")],
    limit: Annotated[int, Query(ge=1, le=10, description="How many decisions.")] = 5,
) -> CourtPracticeResult:
    """Supreme Court decisions with case number, date and snippet.

    none_found means do not mention court practice.
    """
    return get_law_connector_service().find_court_practice(query, limit)


@router.post("/verify-citation", operation_id="verifyCitation", summary="Check a law citation")
async def verify_citation(body: VerifyCitationRequest) -> VerifyCitationResult:
    """Whether the article exists and what it says, with a word-and-number overlap check."""
    return get_law_connector_service().verify_citation(
        body.code, body.article, body.claim, body.paragraph
    )


def connector_openapi() -> dict:
    """OpenAPI 3.1 document of the connector operations only (for a GPT Action)."""
    return get_openapi(
        title=OPENAPI_TITLE,
        version="1.0.0",
        description=OPENAPI_DESCRIPTION,
        routes=router.routes,
        servers=[{"url": settings.connector_public_base_url.rstrip("/")}],
    )


@router.get("/openapi.json", include_in_schema=False)
async def openapi_document() -> dict:
    return connector_openapi()


@discovery_router.get("/.well-known/oauth-protected-resource", include_in_schema=False)
@discovery_router.get("/.well-known/oauth-protected-resource/mcp", include_in_schema=False)
async def oauth_protected_resource() -> dict:
    """Tells MCP clients which sign-in service issues tokens for the connector."""
    return protected_resource_metadata()
