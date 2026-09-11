"""
Main FastAPI Application Entrypoint.
SIH 2026 — AI-Powered Identity Screening & Fraud Resilience System.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import health, samples, upload, screenings
from app.services.firebase_service import init_firebase
import app.data.synthetic_adapter  # Ensures synthetic adapter auto-registers

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multimodal Identity Screening, Forensics, and Risk Assessment API for Border Security",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    init_firebase()


@app.get("/")
async def root():
    return {
        "message": "Welcome to SIH 2026 AI-Powered Identity Screening API",
        "docs": "/docs",
        "health": "/api/health"
    }

# Register API Routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(samples.router, prefix=settings.API_V1_STR, tags=["Data Adapters"])
app.include_router(upload.router, prefix=settings.API_V1_STR, tags=["Document Upload"])
app.include_router(screenings.router, prefix=settings.API_V1_STR, tags=["Screening Pipeline"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
