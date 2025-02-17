import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.momentum.init_momentum import init_all_users_momentum

async def main():
    """Initialize momentum data for all existing users"""
    db = SessionLocal()
    try:
        print("Initializing momentum data for all users...")
        await init_all_users_momentum(db)
        print("Momentum data initialization completed successfully!")
    except Exception as e:
        print(f"Error initializing momentum data: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main()) 