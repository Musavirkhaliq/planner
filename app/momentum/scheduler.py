# scheduler.py

import asyncio
import logging
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .services import MomentumService

logger = logging.getLogger(__name__)

async def run_daily_checks():
    """
    Run daily checks for all users including:
    - Reset weekly points on Monday
    - Reset monthly points on the first of the month
    - Check for perfect week on Sunday
    - Check for perfect month on the last day of the month
    """
    db = SessionLocal()
    try:
        momentum_service = MomentumService(db)
        await momentum_service.schedule_weekly_and_monthly_checks()
        logger.info("Daily momentum checks completed successfully")
    except Exception as e:
        logger.error(f"Error running daily momentum checks: {str(e)}")
    finally:
        db.close()

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