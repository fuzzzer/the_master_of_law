#!/usr/bin/env python3
"""
Backend API client for evaluation.

Calls the real backend API (FastAPI) to test the full RAG pipeline:
  user message → 5-stage RAG → source-specific prompt injection
  → Gemini legal analysis → citation verification → structured response

Usage:
    from backend_client import EvalBackendClient

    client = EvalBackendClient("http://localhost:8000")
    if not client.health_check():
        raise RuntimeError("Backend not running")

    conv_id = client.create_conversation("eval-CRIM-123")
    result = client.send_message(conv_id, situation_text, rag_config={...})
    client.delete_conversation(conv_id)
"""

from __future__ import annotations

import time
from typing import Any

import httpx


class EvalBackendClient:
    """Calls the real backend API for evaluation.

    The backend must be running in dev mode (no Firebase auth required).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 180,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(timeout=timeout)

    # ── Health ────────────────────────────────────────────────

    def health_check(self) -> bool:
        """Verify backend is running and ready."""
        try:
            r = self.client.get(f"{self.base_url}/api/v1/health/ready")
            return r.status_code == 200
        except Exception:
            return False

    def get_collections(self) -> list[dict]:
        """Get available RAG collections and their status."""
        try:
            r = self.client.get(f"{self.base_url}/api/v1/rag/collections")
            r.raise_for_status()
            return r.json().get("collections", [])
        except Exception:
            return []

    # ── Conversation CRUD ────────────────────────────────────

    def create_conversation(self, title: str) -> str:
        """Create a conversation, return its ID."""
        r = self.client.post(
            f"{self.base_url}/api/v1/conversations",
            json={"title": title},
        )
        r.raise_for_status()
        return r.json()["id"]

    def delete_conversation(self, conversation_id: str) -> None:
        """Cleanup after eval. Silently ignores errors."""
        try:
            self.client.delete(
                f"{self.base_url}/api/v1/conversations/{conversation_id}"
            )
        except Exception:
            pass  # Best-effort cleanup

    # ── Chat (full RAG pipeline) ─────────────────────────────

    def send_message(
        self,
        conversation_id: str,
        message: str,
        rag_config: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Send message through the full RAG pipeline with retries.

        Args:
            conversation_id: ID from create_conversation().
            message: The case situation text.
            rag_config: Optional dict controlling which collections to search.
                        Example: {"legal_codes": True, "court_practice": False, "grand_chamber": False}

        Returns:
            {
                "response": str,             # Full AI legal analysis
                "citations": [...],          # Verified citations
                "retrieved_chunks": [...],   # What RAG found (top-20)
                "credits_remaining": int | None,
            }
        """
        body: dict[str, Any] = {"message": message}
        if rag_config is not None:
            body["rag_config"] = rag_config

        last_error = None
        for attempt in range(self.max_retries):
            try:
                r = self.client.post(
                    f"{self.base_url}/api/v1/chat/{conversation_id}/send",
                    json=body,
                )
                r.raise_for_status()
                return r.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 429:
                    wait = (attempt + 1) * 15
                    print(f"    ⏳ Rate limited by backend, waiting {wait}s...")
                    time.sleep(wait)
                elif e.response.status_code >= 500:
                    wait = (attempt + 1) * 5
                    print(f"    ⚠️  Server error {e.response.status_code}, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise  # 4xx (except 429) — don't retry
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                last_error = e
                wait = (attempt + 1) * 10
                print(f"    ⚠️  Connection error, retrying in {wait}s...")
                time.sleep(wait)

        raise RuntimeError(
            f"Failed to send message after {self.max_retries} retries: {last_error}"
        )

    # ── Utility ──────────────────────────────────────────────

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
