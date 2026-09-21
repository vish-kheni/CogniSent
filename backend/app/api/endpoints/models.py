"""Pydantic schemas shared by the API endpoints."""
from pydantic import BaseModel, Field


class SingleReviewRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Review text to analyze")
    session_id: str | None = Field(None, description="Client-generated session identifier")


class BatchReviewRequest(BaseModel):
    texts: list[str] = Field(..., min_items=1, description="List of review texts")
    session_id: str | None = Field(None, description="Client-generated session identifier")


class PredictionResponse(BaseModel):
    id: int
    review: str
    label: str
    confidence: float
    probabilities: dict[str, float]
    session_id: str
    created_at: str


class ReviewListResponse(BaseModel):
    total: int
    items: list[PredictionResponse]


class SessionSummary(BaseModel):
    session_id: str
    total: int
    started_at: str
    last_activity_at: str
    sentiment_counts: dict[str, int]


class StatsResponse(BaseModel):
    total_reviews: int
    sentiment_counts: dict[str, int]
    average_confidence: float


class ModelInfoResponse(BaseModel):
    model: str
    display_name: str
    accuracy: float
    weighted_f1: float
    classes: list[str]
    status: str
