import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Wound AI Platform"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "wound-ai-super-secret-jwt-key-change-in-production-2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # Database: SQLite fallback for local development if Postgres DB is not specified
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./wound_app.db")

    # File Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", os.path.join(BASE_DIR, "storage"))
    IMAGES_DIR: str = os.path.join(STORAGE_DIR, "images")
    MASKS_DIR: str = os.path.join(STORAGE_DIR, "masks")
    OVERLAYS_DIR: str = os.path.join(STORAGE_DIR, "overlays")
    REPORTS_DIR: str = os.path.join(STORAGE_DIR, "reports")

    # AI Mesh / Local AI Config
    AIMESH_BASE_URL: str = os.getenv("AIMESH_BASE_URL", "")
    AIMESH_API_KEY: str = os.getenv("AIMESH_API_KEY", "")

    # CORS Origin list
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*"
    ]

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()

# Ensure storage subdirectories exist
for d in [settings.STORAGE_DIR, settings.IMAGES_DIR, settings.MASKS_DIR, settings.OVERLAYS_DIR, settings.REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)
