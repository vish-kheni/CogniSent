"""FastAPI application entrypoint for the Nike Shoe Review Sentiment API."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.endpoints.reviews import router as reviews_router
from app.services.model_registry import registry

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sentiment analysis API for Nike shoe reviews, backed by a "
    "Conv1D CNN model, with persistent review history.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reviews_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def preload_model():
    """
    Load the CNN model into memory once, at server startup, instead of
    lazily on the first prediction request. Loading TensorFlow + the
    trained model can take 10-20+ seconds on some machines (especially
    Windows without GPU support) -- doing this eagerly means the first
    request from the frontend doesn't time out waiting for it.
    """
    logger.info("Preloading CNN model...")
    registry.get()
    logger.info("CNN model loaded and ready.")


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
