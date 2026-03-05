"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Requests ──
class FeedbackCreate(BaseModel):
    text: str
    source: Optional[str] = "manual"


class FeedbackFilter(BaseModel):
    sentiment: Optional[str] = None
    category: Optional[str] = None
    urgency: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class FeedbackCorrection(BaseModel):
    sentiment: str
    category: str
    urgency: str
    additional_sentiments: Optional[List[str]] = None
    additional_categories: Optional[List[str]] = None


# ── Responses ──
class FeedbackResponse(BaseModel):
    id: int
    text: str
    sentiment: str
    sentiment_confidence: float
    category: str
    category_confidence: float
    urgency: str
    urgency_confidence: float
    source: str
    is_corrected: bool = False
    secondary_sentiments: Optional[List[dict]] = None
    secondary_categories: Optional[List[dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionResult(BaseModel):
    sentiment: str
    sentiment_confidence: float
    category: str
    category_confidence: float
    urgency: str
    urgency_confidence: float
    secondary_sentiments: Optional[List[dict]] = None
    secondary_categories: Optional[List[dict]] = None


class AnalyticsOverview(BaseModel):
    total_feedbacks: int
    sentiment_distribution: dict
    category_distribution: dict
    urgency_distribution: dict
    avg_sentiment_confidence: float


class TrendPoint(BaseModel):
    date: str
    positive: int = 0
    negative: int = 0
    neutral: int = 0


class InsightItem(BaseModel):
    type: str          # warning, improvement, positive
    title: str
    description: str
    priority: str      # high, medium, low
    category: Optional[str] = None


class InsightsResponse(BaseModel):
    insights: List[InsightItem]
    top_issues: List[dict]
    overall_health: str  # good, moderate, critical
