from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from ..dependencies import get_db
from ..auth.dependencies import get_current_user
from . import services
from .schemas import AnalyticsResponse, DailyProductivityAnalytics
from ..users.schemas import User
from typing import List

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/", response_model=AnalyticsResponse)
def get_analytics(
    start_date: date = Query(default_factory=lambda: date.today() - timedelta(days=7)),
    end_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    productivity = services.calculate_productivity_analytics(db, current_user.id, start_date, end_date)
    goal_progress = services.calculate_goal_progress_analytics(db, current_user.id)
    time_slot_distribution = services.calculate_time_slot_distribution(db, current_user.id, start_date, end_date)

    return AnalyticsResponse(
        productivity=productivity,
        goal_progress=goal_progress,
        time_slot_distribution=time_slot_distribution
    )

@router.get("/daily", response_model=List[DailyProductivityAnalytics])
def get_daily_analytics(
    start_date: date = Query(default_factory=lambda: date.today() - timedelta(days=7)),
    end_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    daily_analytics = services.calculate_daily_productivity(db, current_user.id, start_date, end_date)
    return daily_analytics
