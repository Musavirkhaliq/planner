#!/usr/bin/env python
"""
Script to run all momentum scheduler checks.
This can be executed by a cron job or systemd timer instead of
using the in-process scheduler.
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from app.database import SessionLocal
from app.momentum.scheduler import run_daily_checks

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/planner/momentum_checks.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("momentum-checks")

async def main():
    """Run all momentum checks"""
    try:
        logger.info(f"Starting momentum checks at {datetime.now()}")
        await run_daily_checks()
        logger.info(f"Completed momentum checks at {datetime.now()}")
    except Exception as e:
        logger.error(f"Error running momentum checks: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 