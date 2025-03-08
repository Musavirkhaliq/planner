#!/usr/bin/env python
"""
Script to run specific momentum checks.
This can be used to run individual checks manually or via separate schedulers.

Usage:
  python run_specific_momentum_check.py --check=leaderboard
  python run_specific_momentum_check.py --check=streaks
  python run_specific_momentum_check.py --check=weekly
  python run_specific_momentum_check.py --check=monthly
  python run_specific_momentum_check.py --check=all
"""
import asyncio
import logging
import sys
import os
import argparse
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/planner/momentum_specific_checks.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("momentum-specific-checks")

async def run_leaderboard_check():
    """Run only the leaderboard achievement check"""
    from app.database import SessionLocal
    from app.momentum.services import MomentumService
    from app.momentum.scheduler import check_leaderboard_achievements
    
    db = SessionLocal()
    try:
        logger.info("Starting leaderboard achievement check")
        momentum_service = MomentumService(db)
        await check_leaderboard_achievements(db, momentum_service)
        logger.info("Completed leaderboard achievement check")
    except Exception as e:
        logger.error(f"Error running leaderboard achievement check: {str(e)}")
        raise
    finally:
        db.close()

async def run_streaks_check():
    """Run only the expired streaks check"""
    from app.database import SessionLocal
    from app.momentum.services import MomentumService
    from app.momentum.scheduler import check_expired_streaks
    
    db = SessionLocal()
    try:
        logger.info("Starting expired streaks check")
        momentum_service = MomentumService(db)
        await check_expired_streaks(db, momentum_service)
        logger.info("Completed expired streaks check")
    except Exception as e:
        logger.error(f"Error running expired streaks check: {str(e)}")
        raise
    finally:
        db.close()

async def run_weekly_checks():
    """Run weekly points reset and perfect week checks"""
    from app.database import SessionLocal
    from app.momentum.services import MomentumService
    
    db = SessionLocal()
    try:
        logger.info("Starting weekly checks")
        momentum_service = MomentumService(db)
        
        # Get all active users
        from app import models
        users = db.query(models.User).filter(models.User.is_active == True).all()
        
        for user in users:
            try:
                # Check for perfect week (if today is Sunday in user's timezone)
                await momentum_service.check_perfect_week(user.id)
                
                # Reset weekly points if today is Monday in user's timezone
                await momentum_service.reset_periodic_points(user.id)
            except Exception as e:
                logger.error(f"Error processing weekly checks for user {user.id}: {str(e)}")
                continue
                
        logger.info("Completed weekly checks")
    except Exception as e:
        logger.error(f"Error running weekly checks: {str(e)}")
        raise
    finally:
        db.close()

async def run_monthly_checks():
    """Run monthly points reset and perfect month checks"""
    from app.database import SessionLocal
    from app.momentum.services import MomentumService
    
    db = SessionLocal()
    try:
        logger.info("Starting monthly checks")
        momentum_service = MomentumService(db)
        
        # Get all active users
        from app import models
        users = db.query(models.User).filter(models.User.is_active == True).all()
        
        for user in users:
            try:
                # Check for perfect month (if today is last day of month in user's timezone)
                await momentum_service.check_perfect_month(user.id)
                
                # Reset monthly points if today is first day of month in user's timezone
                await momentum_service.reset_periodic_points(user.id)
            except Exception as e:
                logger.error(f"Error processing monthly checks for user {user.id}: {str(e)}")
                continue
                
        logger.info("Completed monthly checks")
    except Exception as e:
        logger.error(f"Error running monthly checks: {str(e)}")
        raise
    finally:
        db.close()

async def run_all_checks():
    """Run all daily momentum checks"""
    from app.momentum.scheduler import run_daily_checks
    
    try:
        logger.info("Starting all momentum checks")
        await run_daily_checks()
        logger.info("Completed all momentum checks")
    except Exception as e:
        logger.error(f"Error running all momentum checks: {str(e)}")
        raise

async def main():
    """Run the specified momentum check"""
    parser = argparse.ArgumentParser(description="Run specific momentum checks")
    parser.add_argument(
        "--check", 
        type=str,
        choices=["leaderboard", "streaks", "weekly", "monthly", "all"],
        required=True,
        help="The specific check to run"
    )
    
    args = parser.parse_args()
    
    try:
        if args.check == "leaderboard":
            await run_leaderboard_check()
        elif args.check == "streaks":
            await run_streaks_check()
        elif args.check == "weekly":
            await run_weekly_checks()
        elif args.check == "monthly":
            await run_monthly_checks()
        elif args.check == "all":
            await run_all_checks()
    except Exception as e:
        logger.error(f"Error running check '{args.check}': {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 