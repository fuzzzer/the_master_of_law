"""
Auth and user schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VerifyTokenRequest(BaseModel):
    """Request for POST /auth/verify-token."""
    id_token: str = Field(..., description="Firebase ID token")


class UserProfile(BaseModel):
    """User profile response."""
    uid: str
    email: str = ""
    display_name: str = ""
    tier: str = "FREE"
    credits_remaining: int = 0
    daily_credits_used: int = 0


class CreditBalance(BaseModel):
    """Credit balance response."""
    tier: str
    credit_balance: int
    daily_credits_used: int
    daily_limit: int | None = None


class CreditTransactionItem(BaseModel):
    """A single credit transaction."""
    amount: int
    transaction_type: str
    description: str = ""
    created_at: str = ""


class CreditHistoryResponse(BaseModel):
    """Response for GET /account/transactions."""
    transactions: list[CreditTransactionItem]
    total: int
