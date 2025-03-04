# router.py

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from . import schemas
from .services import MomentumService
from ..dependencies import get_db
from ..auth.dependencies import get_current_user
from ..models import User

router = APIRouter(prefix="/momentum", tags=["momentum"])

@router.get("/progress", response_model=schemas.UserProgress)
async def get_user_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's progress information"""

    # from app.momentum.init_momentum import init_all_users_momentum
    # from app.database import SessionLocal

    # db = SessionLocal()
    # await init_all_users_momentum(db)

    momentum_service = MomentumService(db)
    return await momentum_service.get_user_progress(current_user.id)

@router.get("/leaderboard", response_model=List[schemas.LeaderboardEntry])
async def get_leaderboard(
    timeframe: str = Query("weekly", enum=["weekly", "monthly", "all-time"]),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get leaderboard data for specified timeframe"""
    momentum_service = MomentumService(db)
    return await momentum_service.get_leaderboard(timeframe, limit, current_user.id)

@router.get("/achievements", response_model=List[schemas.UserAchievement])
async def get_user_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all achievements and their status for current user"""
    momentum_service = MomentumService(db)
    return await momentum_service.get_user_achievements(current_user.id)

@router.get("/streaks", response_model=List[schemas.Streak])
async def get_user_streaks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active streaks for current user"""
    momentum_service = MomentumService(db)
    return await momentum_service.get_user_streaks(current_user.id)

@router.get("/stats", response_model=schemas.MomentumStats)
async def get_momentum_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive momentum statistics for current user"""
    momentum_service = MomentumService(db)
    return await momentum_service.get_momentum_stats(current_user.id)

@router.post("/event", response_model=dict)
async def process_momentum_event(
    event_type: str = Query(..., description="Type of momentum event"),
    metadata: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a momentum event and return updated stats"""
    momentum_service = MomentumService(db)
    return await momentum_service.process_event(current_user.id, event_type, metadata)

@router.get("/levels", response_model=List[schemas.Level])
async def get_levels(
    db: Session = Depends(get_db)
):
    """Get all available levels and their requirements"""
    momentum_service = MomentumService(db)
    return await momentum_service.get_levels()

@router.get("/achievements/available", response_model=List[schemas.Achievement])
async def get_available_achievements(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all available achievements, optionally filtered by category"""
    momentum_service = MomentumService(db)
    return await momentum_service.get_available_achievements(category)

@router.post("/admin/run-scheduled-checks", response_model=dict)
async def run_scheduled_checks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to manually trigger the scheduled checks for weekly/monthly goals
    This can also be called by a cron job or scheduler
    """
    # Check admin status (implement proper authorization as needed)
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    momentum_service = MomentumService(db)
    await momentum_service.schedule_weekly_and_monthly_checks()
    
    return {"status": "success", "message": "Scheduled checks completed"}

@router.post("/check-perfect-week/{user_id}", response_model=dict)
async def check_perfect_week(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a user has completed a perfect week and award points if applicable"""
    # Only allow users to check their own perfect week status or admins
    if current_user.id != user_id and not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    momentum_service = MomentumService(db)
    is_perfect = await momentum_service.check_perfect_week(user_id)
    
    return {
        "user_id": user_id,
        "perfect_week": is_perfect,
        "message": "Perfect week achieved!" if is_perfect else "Perfect week not achieved"
    }
