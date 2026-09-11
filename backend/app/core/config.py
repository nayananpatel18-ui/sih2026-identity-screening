"""
Core application settings and configuration management.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH 2026 AI-Powered Identity Screening & Fraud Resilience System"
    API_V1_STR: str = "/api"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]
    
    # Dataset paths
    SYNTHETIC_DATASET_PATH: str = "datasets/synthetic/manifest.json"

    # Upload settings (demo-safe local storage)
    UPLOAD_MAX_BYTES: int = 5 * 1024 * 1024
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = ["png", "jpg", "jpeg", "webp"]

    # Missing Admin credentials means explicit LOCAL fallback, never a fake identity.
    FIREBASE_PROJECT_ID: str | None = None
    FIREBASE_CREDENTIALS_PATH: str | None = None
    FIREBASE_USE_APPLICATION_DEFAULT: bool = False
    FIREBASE_STORAGE_BUCKET: str | None = None
    FIREBASE_LOCAL_FALLBACK: bool = True
    FIREBASE_EMULATOR: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
