# scheduler.py

import asyncio
import logging
import time
from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import SessionLocal
from .services import MomentumService
from .. import models

logger = logging.getLogger(__name__)

async def run_daily_checks():
    """
    Run daily checks for all users including:
    - Reset weekly points on Monday
    - Reset monthly points on the first of the month
    - Check for perfect week on Sunday
    - Check for perfect month on the last day of the month
    - Check for leaderboard positions and award achievements
    """
    db = SessionLocal()
    try:
        logger.info("Starting daily momentum checks")
        
        # Create momentum service
        momentum_service = MomentumService(db)
        
        # Get the current date in UTC
        today_utc = datetime.utcnow().date()
        
        # Process weekly and monthly checks
        await momentum_service.schedule_weekly_and_monthly_checks()
        
        # Check leaderboard achievements (only on Sunday after the week has ended)
        if today_utc.weekday() == 6:  # Sunday
            await check_leaderboard_achievements(db, momentum_service)
            
        # Check for expired streaks (streaks that haven't been maintained)
        await check_expired_streaks(db, momentum_service)
        
        logger.info("Daily momentum checks completed successfully")
    except Exception as e:
        logger.error(f"Error running daily momentum checks: {str(e)}")
    finally:
        db.close()

async def check_leaderboard_achievements(db: Session, momentum_service: MomentumService):
    """
    Check if any users have achieved #1 on the weekly leaderboard
    and award the Leaderboard Legend achievement
    """
    logger.info("Checking leaderboard achievements")
    
    try:
        # Get the top user on the weekly leaderboard
        top_user = db.query(models.User).order_by(
            models.User.weekly_points.desc()
        ).first()
        
        if not top_user or top_user.weekly_points < 100:
            # Don't award if no users or if points are too low (to prevent awarding in inactive weeks)
            logger.info("No users qualified for leaderboard achievements this week")
            return
            
        # Get the Leaderboard Legend achievement
        leaderboard_achievement = db.query(models.Achievement).filter(
            models.Achievement.name == 'Leaderboard Legend'
        ).first()
        
        if not leaderboard_achievement:
            logger.error("Leaderboard Legend achievement not found in database")
            return
            
        # Check if user already has this achievement
        existing = db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == top_user.id,
            models.UserAchievement.achievement_id == leaderboard_achievement.id,
            models.UserAchievement.completed == True
        ).first()
        
        if existing:
            logger.info(f"User {top_user.id} already has Leaderboard Legend achievement")
            return
            
        # Award the achievement
        logger.info(f"Awarding Leaderboard Legend achievement to user {top_user.id}")
        
        # Create the user achievement
        user_achievement = models.UserAchievement(
            user_id=top_user.id,
            achievement_id=leaderboard_achievement.id,
            progress=1,
            completed=True,
            completed_at=datetime.utcnow()
        )
        db.add(user_achievement)
        db.commit()
        
        # Award points for the achievement
        await momentum_service.award_points(top_user.id, leaderboard_achievement.points)
        
        logger.info(f"Successfully awarded Leaderboard Legend to user {top_user.id}")
    except Exception as e:
        logger.error(f"Error checking leaderboard achievements: {str(e)}")

async def check_expired_streaks(db: Session, momentum_service: MomentumService):
    """
    Check for streaks that haven't been maintained and reset them
    """
    logger.info("Checking for expired streaks")
    
    try:
        # Get the current date in UTC
        today_utc = datetime.utcnow().date()
        
        # Find all streaks where the last activity was more than 1 day ago
        expired_streaks = db.query(models.Streak).filter(
            models.Streak.current_count > 0,
            models.Streak.last_activity_date < today_utc - timedelta(days=1)
        ).all()
        
        for streak in expired_streaks:
            # Reset the streak but keep the longest count
            logger.info(f"Resetting expired streak for user {streak.user_id}, type: {streak.streak_type}")
            streak.current_count = 0
            # Don't update last_activity_date to avoid immediately restarting the streak
            
        db.commit()
        logger.info(f"Reset {len(expired_streaks)} expired streaks")
    except Exception as e:
        logger.error(f"Error checking expired streaks: {str(e)}")

async def schedule_daily_checks():
    """
    Schedule daily checks to run at a specified time every day
    In a production environment, this should be replaced with a proper task scheduler
    like Celery, APScheduler, or a cron job
    """
    while True:
        now = datetime.now()
        # Run at 2 AM every day
        target_time = now.replace(hour=2, minute=0, second=0, microsecond=0)
        
        # If it's already past 2 AM, wait until tomorrow
        if now >= target_time:
            target_time = target_time + timedelta(days=1)
        
        # Calculate seconds to wait
        wait_seconds = (target_time - now).total_seconds()
        logger.info(f"Next momentum check scheduled for {target_time} (in {wait_seconds} seconds)")
        
        # Wait until the scheduled time
        await asyncio.sleep(wait_seconds)
        
        # Run the daily checks
        await run_daily_checks()

async def initialize_scheduler():
    """
    Initialize the scheduler when the application starts
    This function should be called when the application starts
    """
    # Start the scheduler in a background task
    asyncio.create_task(schedule_daily_checks())
    logger.info("Momentum scheduler initialized") 