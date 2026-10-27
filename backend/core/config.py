"""Application settings – reads from env vars / .env with sensible defaults."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── MongoDB ──────────────────────────────────────────────────────
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "uniflow"

    # ── JWT ──────────────────────────────────────────────────────────
    JWT_SECRET: str = "super-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080       # 7 days

    # ── Superadmin seed ──────────────────────────────────────────────
    SUPERADMIN_EMAIL: str = "admin@uniflow.local"
    SUPERADMIN_PASSWORD: str = "changeme-in-production"

    # ── Cloudinary (file storage) ─────────────────────────────────────
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ── Redis ─────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Frontend / CORS ──────────────────────────────────────────────
    FRONTEND_URL: str = ""

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
