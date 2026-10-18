"""
Global error handling middleware.

Catches unhandled exceptions and returns structured JSON error responses
instead of letting FastAPI return raw 500 HTML.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.utils.logger import get_logger
from app.utils.provider_errors import classify

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catch-all exception handler for unhandled errors."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            return await call_next(request)
        except Exception as exc:
            provider = classify(exc)

            if provider.is_provider_fault:
                # An upstream limit or outage is an expected operating
                # condition, not a defect in this service. Returning 500 for
                # it told the user nothing, told the operator nothing, and
                # read as a bug in the app rather than a budget that resets.
                logger.warning(
                    "provider_error",
                    path=request.url.path,
                    method=request.method,
                    kind=provider.kind.value,
                    retry_after_s=provider.retry_after_s,
                    error=str(exc)[:300],
                )
                headers = (
                    {"Retry-After": str(provider.retry_after_s)}
                    if provider.retry_after_s
                    else None
                )
                return JSONResponse(
                    status_code=provider.status_code,
                    content={
                        "error": provider.error_code,
                        "message": provider.message_ka,
                        **(
                            {"retry_after_s": provider.retry_after_s}
                            if provider.retry_after_s
                            else {}
                        ),
                    },
                    headers=headers,
                )

            # Anything we cannot attribute upstream stays a 500 with a full
            # traceback — dressing a real bug up as "try again later" is how
            # defects get shipped.
            logger.error(
                "unhandled_exception",
                path=request.url.path,
                method=request.method,
                error=str(exc),
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": provider.message_ka,
                },
            )
