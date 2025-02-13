from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.analytics.services import AnalyticsService
from app.analytics.schemas import TimeSlotAnalytics, DailyAnalytics, TimeRangeAnalytics

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview", response_model=TimeSlotAnalytics)
def get_overview_analytics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overview analytics for the current user's time slots."""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_user_analytics(current_user.id)

@router.get("/daily/{date}", response_model=DailyAnalytics)
def get_daily_analytics(
    date: date,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific day."""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_daily_analytics(current_user.id, date)

@router.get("/range", response_model=TimeRangeAnalytics)
def get_range_analytics(
    start_date: date,
    end_date: date,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific date range."""
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be before or equal to end date"
        )
        
    analytics_service = AnalyticsService(db)
    return analytics_service.get_time_range_analytics(
        current_user.id,
        start_date,
        end_date
    )

@router.get("/today", response_model=DailyAnalytics)
def get_today_analytics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for the current day."""
    today = date.today()
    analytics_service = AnalyticsService(db)
    return analytics_service.get_daily_analytics(current_user.id, today)
