"""Application configuration, loaded from environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings:
    PROJECT_NAME: str = "Nike Shoe Review Sentiment API"
    API_V1_PREFIX: str = "/api"

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    USE_CNN: bool = os.getenv("USE_CNN", "false").lower() in {"1", "true", "yes"}

    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000"
    ).split(",")

    MODELS_DIR: Path = BASE_DIR / "models"
    REGISTRY_PATH: Path = MODELS_DIR / "registry.json"
    DATA_PATH: Path = BASE_DIR / "data" / "nike_shoe_review.xlsx"
    HISTORY_DB_PATH: Path = BASE_DIR / "data" / "history.db"


settings = Settings()
