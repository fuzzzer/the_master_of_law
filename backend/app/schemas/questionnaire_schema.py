"""
Pydantic schemas for the questionnaire API.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class QuestionSchema(BaseModel):
    """A single question in the questionnaire."""

    id: str = Field(..., description="Unique question identifier")
    question_text_ka: str = Field(..., min_length=1, description="Question text in Georgian")
    question_type: str = Field(..., pattern=r"^(text|boolean|choice|date|number)$")
    options: list[str] = Field(default_factory=list, description="Options for choice questions")
    required: bool = Field(default=True)
    purpose: str = Field(default="", description="Why this question is asked")
    legal_relevance: str = Field(default="", description="Legal relevance of this question")
    sort_order: int = Field(default=0)

    @field_validator("options")
    @classmethod
    def validate_choice_options(cls, v: list[str], info: Any) -> list[str]:
        values = info.data
        if values.get("question_type") == "choice" and len(v) < 2:
            raise ValueError("Choice questions must have at least 2 options")
        return v


class AnswerSchema(BaseModel):
    """User answer to a single question."""

    question_id: str
    answer: str = Field(..., min_length=1)


class QuestionnaireGenerateResponse(BaseModel):
    """Response for POST /questionnaire/{id}/generate."""

    questions: list[QuestionSchema]
    total: int
    required_count: int


class QuestionnaireGetResponse(BaseModel):
    """Response for GET /questionnaire/{id}."""

    questions: list[QuestionSchema]
    answers: list[AnswerSchema]
    progress: dict[str, int] = Field(..., description="{answered: X, total: Y}")


class QuestionnaireAnswerRequest(BaseModel):
    """Request body for POST /questionnaire/{id}/answer."""

    question_id: str
    answer: str = Field(..., min_length=1)


class QuestionnaireAnswerResponse(BaseModel):
    """Response for POST /questionnaire/{id}/answer."""

    accepted: bool
    next_question: QuestionSchema | None = None
    follow_ups: list[QuestionSchema] = Field(default_factory=list)
    progress: dict[str, int]


class QuestionnaireSkipResponse(BaseModel):
    """Response for POST /questionnaire/{id}/skip."""

    skipped_count: int
    ready_for_analysis: bool
    progress: dict[str, int] = Field(default_factory=dict, description="{answered: X, total: Y}")
