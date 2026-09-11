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
    
    # Firebase settings (Optional fallback)
    FIREBASE_PROJECT_ID: str = "sih2026-identity-screening"
    FIREBASE_CREDENTIALS_PATH: str = "backend/firebase-credentials.json"
    FIREBASE_EMULATOR: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
