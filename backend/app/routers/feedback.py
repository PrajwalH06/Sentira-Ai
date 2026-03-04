"""
Feedback API router – submit, list, filter feedback.
"""
import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.sql import func
from datetime import datetime

from app.database import get_db
from app.models import Feedback
from app.schemas import FeedbackCreate, FeedbackResponse, PredictionResult, FeedbackCorrection
from app.ml.predictor import predict, add_correction

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(data: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    """Submit a single feedback text for AI analysis."""
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Feedback text cannot be empty")

    # Run ML prediction
    result = predict(data.text)

    # Store in DB
    feedback = Feedback(
        text=data.text,
        sentiment=result["sentiment"],
        sentiment_confidence=result["sentiment_confidence"],
        category=result["category"],
        category_confidence=result["category_confidence"],
        urgency=result["urgency"],
        urgency_confidence=result["urgency_confidence"],
        source=data.source or "manual",
        is_corrected=False,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return feedback


@router.post("/csv", response_model=list[FeedbackResponse])
async def upload_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Upload a CSV file with feedback texts for batch processing."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    text_content = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text_content))

    # Find the text column (flexible naming)
    text_column = None
    if reader.fieldnames:
        for col in reader.fieldnames:
            if col.lower().strip() in ["text", "feedback", "message", "content", "review", "comment"]:
                text_column = col
                break
        if text_column is None and reader.fieldnames:
            text_column = reader.fieldnames[0]  # Default to first column

    if text_column is None:
        raise HTTPException(status_code=400, detail="CSV must have a header row")

    results = []
    for row in reader:
        text = row.get(text_column, "").strip()
        if not text:
            continue

        prediction = predict(text)
        feedback = Feedback(
            text=text,
            sentiment=prediction["sentiment"],
            sentiment_confidence=prediction["sentiment_confidence"],
            category=prediction["category"],
            category_confidence=prediction["category_confidence"],
            urgency=prediction["urgency"],
            urgency_confidence=prediction["urgency_confidence"],
            source="csv",
            is_corrected=False,
        )
        db.add(feedback)
        results.append(feedback)

    await db.commit()
    for fb in results:
        await db.refresh(fb)

    return results


@router.get("/", response_model=list[FeedbackResponse])
async def list_feedbacks(
    sentiment: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List feedbacks with optional filters."""
    query = select(Feedback).order_by(desc(Feedback.created_at))

    if sentiment:
        query = query.where(Feedback.sentiment == sentiment)
    if category:
        query = query.where(Feedback.category == category)
    if urgency:
        query = query.where(Feedback.urgency == urgency)
    if start_date:
        query = query.where(Feedback.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(Feedback.created_at <= datetime.fromisoformat(end_date))

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/count")
async def feedback_count(db: AsyncSession = Depends(get_db)):
    """Get total feedback count."""
    result = await db.execute(select(func.count(Feedback.id)))
    return {"count": result.scalar()}


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(feedback_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single feedback by ID."""
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback


@router.put("/{feedback_id}/correct", response_model=FeedbackResponse)
async def correct_feedback(feedback_id: int, correction: FeedbackCorrection, db: AsyncSession = Depends(get_db)):
    """Correct an AI prediction. Updates the DB and the active predictor cache for instant learning."""
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    feedback.sentiment = correction.sentiment
    feedback.sentiment_confidence = 1.0  # Master confidence because it's human-corrected
    feedback.category = correction.category
    feedback.category_confidence = 1.0
    feedback.urgency = correction.urgency
    feedback.urgency_confidence = 1.0
    feedback.is_corrected = True
    
    await db.commit()
    await db.refresh(feedback)
    
    # Instantly update memory cache in predictor for self-learning
    add_correction(feedback.text, correction.sentiment, correction.category, correction.urgency)
    
    return feedback


@router.post("/analyze", response_model=PredictionResult)
async def analyze_text(data: FeedbackCreate):
    """Analyze text without saving to database (preview mode)."""
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    return predict(data.text)
