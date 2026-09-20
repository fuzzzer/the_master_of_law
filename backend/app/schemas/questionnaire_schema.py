"""
Questionnaire Pydantic schemas for API request/response validation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class QuestionSchema(BaseModel):
    """A single questionnaire question."""
    question_id: str
    question_text: str
    question_type: str = "text"
    options: list[str] | None = None
    required: bool = True
    purpose: str | None = None
    legal_relevance: str | None = None


class AnswerSchema(BaseModel):
    """A submitted answer."""
    question_id: str
    question_text: str = ""
    answer_value: str | None = None
    answer_type: str = "text"
    skipped: bool = False
    answered_at: str = ""


class ProgressSchema(BaseModel):
    """Questionnaire completion progress."""
    answered: int = 0
    skipped: int = 0
    total: int = 0
    remaining: int = 0


class GenerateRequest(BaseModel):
    """Request for POST /questionnaire/{id}/generate."""
    domain: str = Field(default="civil", description="Legal domain key (criminal, civil, labor, etc.)")
    user_description: str = Field(..., min_length=5, max_length=10000)


class GenerateResponse(BaseModel):
    """Response for POST /questionnaire/{id}/generate."""
    questions: list[QuestionSchema]
    total: int
    required_count: int


class QuestionnaireStateResponse(BaseModel):
    """Response for GET /questionnaire/{id}."""
    questions: list[QuestionSchema]
    answers: list[AnswerSchema]
    progress: ProgressSchema


class AnswerRequest(BaseModel):
    """Request for POST /questionnaire/{id}/answer."""
    question_id: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=0, max_length=10000)


class AnswerResponse(BaseModel):
    """Response for POST /questionnaire/{id}/answer."""
    accepted: bool
    next_question: QuestionSchema | None = None
    follow_ups: list[QuestionSchema] = Field(default_factory=list)
    error: str | None = None


class SkipResponse(BaseModel):
    """Response for POST /questionnaire/{id}/skip."""
    skipped_count: int
    ready_for_analysis: bool


class ExtractRequest(BaseModel):
    """Request for POST /questionnaire/{id}/extract."""
    domain: str = Field(default="civil", description="Legal domain key")
    narrative: str = Field(..., min_length=10, max_length=20000)


class ExtractedAnswerSchema(BaseModel):
    """A single extracted answer from narrative."""
    question_id: str
    question_text: str
    answer_value: str
    answer_type: str = "text"


class ExtractResponse(BaseModel):
    """Response for POST /questionnaire/{id}/extract."""
    extracted_count: int
    total_questions: int
    questions: list[QuestionSchema]
    extracted_answers: list[ExtractedAnswerSchema]
