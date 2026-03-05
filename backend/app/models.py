"""
SQLAlchemy ORM models for Sentira AI.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    text = Column(Text, nullable=False)
    sentiment = Column(String(20), nullable=False)           # positive, negative, neutral
    sentiment_confidence = Column(Float, default=0.0)
    category = Column(String(50), nullable=False)            # UI/UX, Bugs, Performance, etc.
    category_confidence = Column(Float, default=0.0)
    urgency = Column(String(20), nullable=False)             # low, medium, high, critical
    urgency_confidence = Column(Float, default=0.0)
    source = Column(String(50), default="manual")            # manual, csv, api
    is_corrected = Column(Boolean, default=False)            # For self-learning AI overrides
    secondary_sentiments = Column(Text, nullable=True)       # JSON string of [{label, confidence}]
    secondary_categories = Column(Text, nullable=True)       # JSON string of [{label, confidence}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
