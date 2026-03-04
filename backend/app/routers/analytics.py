"""
Analytics API router – trends, insights, overview stats.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, cast, String
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Feedback
from app.schemas import AnalyticsOverview, TrendPoint, InsightItem, InsightsResponse

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """Get overall analytics: totals, distributions, averages."""
    # Total count
    count_result = await db.execute(select(func.count(Feedback.id)))
    total = count_result.scalar() or 0

    if total == 0:
        return AnalyticsOverview(
            total_feedbacks=0,
            sentiment_distribution={"positive": 0, "negative": 0, "neutral": 0},
            category_distribution={},
            urgency_distribution={"low": 0, "medium": 0, "high": 0, "critical": 0},
            avg_sentiment_confidence=0.0,
        )

    # Sentiment distribution
    sent_result = await db.execute(
        select(Feedback.sentiment, func.count(Feedback.id))
        .group_by(Feedback.sentiment)
    )
    sentiment_dist = dict(sent_result.all())

    # Category distribution
    cat_result = await db.execute(
        select(Feedback.category, func.count(Feedback.id))
        .group_by(Feedback.category)
    )
    category_dist = dict(cat_result.all())

    # Urgency distribution
    urg_result = await db.execute(
        select(Feedback.urgency, func.count(Feedback.id))
        .group_by(Feedback.urgency)
    )
    urgency_dist = dict(urg_result.all())

    # Average confidence
    avg_result = await db.execute(select(func.avg(Feedback.sentiment_confidence)))
    avg_conf = avg_result.scalar() or 0.0

    return AnalyticsOverview(
        total_feedbacks=total,
        sentiment_distribution=sentiment_dist,
        category_distribution=category_dist,
        urgency_distribution=urgency_dist,
        avg_sentiment_confidence=round(float(avg_conf), 4),
    )


@router.get("/trends")
async def get_trends(
    days: int = Query(30, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get daily sentiment trends over a time period."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(Feedback).where(Feedback.created_at >= cutoff).order_by(Feedback.created_at)
    )
    feedbacks = result.scalars().all()

    # Aggregate by date
    daily = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    for fb in feedbacks:
        date_key = fb.created_at.strftime("%Y-%m-%d") if fb.created_at else "unknown"
        daily[date_key][fb.sentiment] += 1

    # Also calculate category trends
    cat_daily = defaultdict(lambda: defaultdict(int))
    for fb in feedbacks:
        date_key = fb.created_at.strftime("%Y-%m-%d") if fb.created_at else "unknown"
        cat_daily[date_key][fb.category] += 1

    trends = []
    for date_key in sorted(daily.keys()):
        trends.append({
            "date": date_key,
            **daily[date_key],
        })

    category_trends = []
    for date_key in sorted(cat_daily.keys()):
        category_trends.append({
            "date": date_key,
            **dict(cat_daily[date_key]),
        })

    return {
        "sentiment_trends": trends,
        "category_trends": category_trends,
    }


@router.get("/insights", response_model=InsightsResponse)
async def get_insights(db: AsyncSession = Depends(get_db)):
    """Generate actionable insights from feedback data."""
    result = await db.execute(select(Feedback).order_by(Feedback.created_at.desc()))
    feedbacks = result.scalars().all()
    total = len(feedbacks)

    if total == 0:
        return InsightsResponse(
            insights=[InsightItem(
                type="info",
                title="No Data Yet",
                description="Submit feedback to start generating insights.",
                priority="low",
            )],
            top_issues=[],
            overall_health="moderate",
        )

    # Calculate distributions
    sentiments = Counter(fb.sentiment for fb in feedbacks)
    categories = Counter(fb.category for fb in feedbacks)
    urgencies = Counter(fb.urgency for fb in feedbacks)

    # Track negative feedback by category
    neg_by_category = Counter(
        fb.category for fb in feedbacks if fb.sentiment == "negative"
    )

    insights = []

    # ── Sentiment-based insights ──
    neg_pct = (sentiments.get("negative", 0) / total) * 100 if total > 0 else 0
    pos_pct = (sentiments.get("positive", 0) / total) * 100 if total > 0 else 0

    if neg_pct > 50:
        insights.append(InsightItem(
            type="warning",
            title="High Negative Sentiment",
            description=f"{neg_pct:.0f}% of feedback is negative. Immediate action required to address customer dissatisfaction.",
            priority="high",
        ))
    elif neg_pct > 30:
        insights.append(InsightItem(
            type="warning",
            title="Rising Negative Sentiment",
            description=f"{neg_pct:.0f}% of feedback is negative. Consider investigating top complaint areas.",
            priority="medium",
        ))

    if pos_pct > 60:
        insights.append(InsightItem(
            type="positive",
            title="Strong Positive Sentiment",
            description=f"{pos_pct:.0f}% of feedback is positive. Customers are generally satisfied.",
            priority="low",
        ))

    # ── Category-based insights ──
    for cat, count in neg_by_category.most_common(3):
        pct = (count / total) * 100
        if pct > 10:
            insights.append(InsightItem(
                type="improvement",
                title=f"Frequent Issues in {cat}",
                description=f"{cat} accounts for {pct:.0f}% of negative feedback ({count} reports). Focus improvements here.",
                priority="high" if pct > 20 else "medium",
                category=cat,
            ))

    # ── Urgency-based insights ──
    critical_count = urgencies.get("critical", 0) + urgencies.get("high", 0)
    if critical_count > 0:
        crit_pct = (critical_count / total) * 100
        insights.append(InsightItem(
            type="warning",
            title=f"{critical_count} High-Urgency Items",
            description=f"{crit_pct:.0f}% of feedback is marked as high or critical urgency. These require immediate attention.",
            priority="high",
        ))

    # ── Category recommendations ──
    top_cat = categories.most_common(1)[0] if categories else None
    if top_cat:
        insights.append(InsightItem(
            type="improvement",
            title=f"Most Discussed: {top_cat[0]}",
            description=f"{top_cat[0]} is the most mentioned category ({top_cat[1]} mentions). Prioritize improvements in this area.",
            priority="medium",
            category=top_cat[0],
        ))

    # If no specific insights generated
    if not insights:
        insights.append(InsightItem(
            type="positive",
            title="Feedback Looking Healthy",
            description="No major issues detected. Continue monitoring for changes.",
            priority="low",
        ))

    # ── Top issues (negative items) ──
    top_issues = []
    for cat, count in neg_by_category.most_common(5):
        top_issues.append({
            "category": cat,
            "count": count,
            "percentage": round((count / total) * 100, 1),
        })

    # ── Overall health ──
    if neg_pct > 50 or critical_count > total * 0.3:
        health = "critical"
    elif neg_pct > 30:
        health = "moderate"
    else:
        health = "good"

    return InsightsResponse(
        insights=insights,
        top_issues=top_issues,
        overall_health=health,
    )


@router.get("/model-info")
async def model_info():
    """Get information about loaded ML models."""
    from app.ml.predictor import get_model_info
    return get_model_info()
