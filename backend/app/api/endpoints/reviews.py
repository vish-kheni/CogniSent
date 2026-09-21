"""API routes for review sentiment analysis, session history, and model info."""
from fastapi import APIRouter, HTTPException, Query

from app.api.endpoints.models import (
    SingleReviewRequest,
    BatchReviewRequest,
    PredictionResponse,
    ReviewListResponse,
    SessionSummary,
    StatsResponse,
    ModelInfoResponse,
)
from app.services import sentiment_service
from app.services.model_registry import registry

router = APIRouter()


@router.post("/reviews/analyze", response_model=PredictionResponse, tags=["reviews"])
def analyze_review(payload: SingleReviewRequest):
    try:
        result = sentiment_service.analyze_text(payload.text, payload.session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/reviews/analyze-batch", response_model=list[PredictionResponse], tags=["reviews"])
def analyze_batch(payload: BatchReviewRequest):
    if len(payload.texts) > 500:
        raise HTTPException(status_code=400, detail="Batch size limited to 500 reviews")
    try:
        results = sentiment_service.analyze_batch(payload.texts, payload.session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return results


@router.get("/reviews", response_model=ReviewListResponse, tags=["reviews"])
def get_reviews(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    label: str | None = Query(None, description="Filter by Positive/Negative/Neutral"),
    session_id: str | None = Query(None, description="Filter by session"),
):
    return sentiment_service.list_reviews(
        limit=limit, offset=offset, label=label, session_id=session_id
    )


@router.get("/sessions", response_model=list[SessionSummary], tags=["reviews"])
def get_sessions(limit: int = Query(20, ge=1, le=100)):
    return sentiment_service.list_sessions(limit=limit)


@router.delete("/reviews", tags=["reviews"])
def clear_reviews():
    sentiment_service.clear_reviews()
    return {"status": "cleared"}


@router.delete("/reviews/{review_id}", tags=["reviews"])
def delete_review(review_id: int):
    deleted = sentiment_service.delete_review(review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Review {review_id} not found")
    return {"status": "deleted", "id": review_id}


@router.delete("/sessions/{session_id}", tags=["reviews"])
def delete_session(session_id: str):
    deleted_count = sentiment_service.delete_session(session_id)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {"status": "deleted", "session_id": session_id, "reviews_deleted": deleted_count}


@router.get("/stats", response_model=StatsResponse, tags=["analytics"])
def get_stats():
    return sentiment_service.get_stats()


@router.get("/model", response_model=ModelInfoResponse, tags=["model"])
def get_model_info():
    return registry.info()
