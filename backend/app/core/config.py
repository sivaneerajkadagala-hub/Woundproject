import os
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Wound AI Platform"
    API_V1_STR: str = "/api"
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

    # U-Net checkpoint (optional). When set and file exists, U-Net inference
    # is used. Otherwise CV color segmentation is the reliable fallback.
    UNET_CHECKPOINT_PATH: str = os.getenv("UNET_CHECKPOINT_PATH", "")

    # SECRET_KEY is loaded from env/.env. No hardcoded production fallback.
    SECRET_KEY: str = ""

    # Comma-separated CORS origins string (parsed into _cors_origins list).
    # No wildcard (*) is allowed.
    CORS_ORIGINS_STR: str = ""

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    # Resolved CORS origins list (populated by _build_settings)
    CORS_ORIGINS: list[str] = []


def _build_settings() -> Settings:
    s = Settings()

    # SECRET_KEY must come from the environment or .env file.
    # A dev-only fallback is permitted ONLY when running under pytest or
    # when DEV_ALLOW_INSECURE_SECRET=1 is explicitly set. This fallback is
    # never appropriate for production.
    if not s.SECRET_KEY:
        is_test = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None
        dev_allowed = os.getenv("DEV_ALLOW_INSECURE_SECRET", "0") == "1"
        if is_test or dev_allowed:
            s.SECRET_KEY = "dev-only-insecure-secret-do-not-use-in-production"
        else:
            raise RuntimeError(
                "SECRET_KEY environment variable is required. "
                "Set it in your .env file or environment. "
                "Example: SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')"
            )

    # Parse CORS_ORIGINS from the comma-separated string, or use dev defaults.
    cors_str = s.CORS_ORIGINS_STR or os.getenv("CORS_ORIGINS", "")
    if cors_str:
        s.CORS_ORIGINS = [o.strip() for o in cors_str.split(",") if o.strip()]
    else:
        s.CORS_ORIGINS = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]

    # Reject wildcard origin for security
    if "*" in s.CORS_ORIGINS:
        raise RuntimeError(
            "Wildcard CORS origin '*' is not allowed. "
            "Set explicit origins via CORS_ORIGINS env variable."
        )

    return s


settings = _build_settings()

# Ensure storage subdirectories exist
for d in [settings.STORAGE_DIR, settings.IMAGES_DIR, settings.MASKS_DIR, settings.OVERLAYS_DIR, settings.REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)
