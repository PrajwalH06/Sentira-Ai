"""
Sentira AI – FastAPI Application Entry Point
Professional-grade ensemble ML with sarcasm detection.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.ml.predictor import load_models
from app.routers import feedback, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("🚀 Starting Sentira AI...")
    await init_db()
    load_models()
    print("✅ Sentira AI is ready!")
    yield
    # Shutdown
    print("👋 Shutting down Sentira AI...")


app = FastAPI(
    title="Sentira AI",
    description="Self-Hosted Customer Feedback Intelligence System — Professional-grade ensemble ML with sarcasm detection",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(feedback.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    return {
        "name": "Sentira AI",
        "version": "2.0.0",
        "status": "running",
        "description": "Self-Hosted Customer Feedback Intelligence System",
        "ml_engine": "Ensemble VotingClassifier (LinearSVC + LogReg + NB + ComplementNB)",
        "capabilities": ["sentiment", "category", "urgency", "sarcasm_detection"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
