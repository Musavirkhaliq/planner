#!/usr/bin/env python
import asyncio
import sys
import os
import sqlite3
import json
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the momentum constants but not any SQLAlchemy models
from app.momentum.momentum import LEVELS, ACHIEVEMENTS

async def init_all_users_momentum_direct():
    """Initialize momentum data for all existing users using direct SQLite commands"""
    print("Initializing momentum data for all users using direct SQLite...")
    
    # Connect to SQLite database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. First, ensure all levels exist
    for level_data in LEVELS:
        cursor.execute(
            "SELECT id FROM levels WHERE level_number = ?", 
            (level_data['level_number'],)
        )
        result = cursor.fetchone()
        
        if not result:
            # Create new level
            cursor.execute(
                """
                INSERT INTO levels (level_number, points_required, title, perks) 
                VALUES (?, ?, ?, ?)
                """, 
                (
                    level_data['level_number'], 
                    level_data['points_required'], 
                    level_data['title'], 
                    json.dumps(level_data['perks'])
                )
            )
    
    # 2. Ensure all achievements exist
    for idx, achievement_data in enumerate(ACHIEVEMENTS):
        cursor.execute(
            "SELECT id FROM achievements WHERE name = ?", 
            (achievement_data['name'],)
        )
        result = cursor.fetchone()
        
        achievement_id = None
        if not result:
            # Create new achievement
            cursor.execute(
                """
                INSERT INTO achievements (name, description, points, category, criteria_type, criteria_value, icon_name) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, 
                (
                    achievement_data['name'],
                    achievement_data['description'],
                    achievement_data['points'],
                    achievement_data['category'],
                    achievement_data['criteria_type'],
                    achievement_data['criteria_value'],
                    achievement_data['icon_name']
                )
            )
            achievement_id = cursor.lastrowid
        else:
            achievement_id = result[0]
    
    # 3. Get all users and initialize their momentum data
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    
    users_initialized = 0
    for user_id_tuple in users:
        user_id = user_id_tuple[0]
        
        # Initialize points if not set
        cursor.execute(
            """
            UPDATE users 
            SET total_points = COALESCE(total_points, 0),
                weekly_points = COALESCE(weekly_points, 0),
                monthly_points = COALESCE(monthly_points, 0) 
            WHERE id = ?
            """, 
            (user_id,)
        )
        
        # Initialize level if not set
        cursor.execute("SELECT current_level_id FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        if not result[0]:  # If current_level_id is NULL
            # Get level 1
            cursor.execute("SELECT id FROM levels WHERE level_number = 1")
            level_1_result = cursor.fetchone()
            
            if level_1_result:
                level_1_id = level_1_result[0]
                cursor.execute(
                    "UPDATE users SET current_level_id = ? WHERE id = ?",
                    (level_1_id, user_id)
                )
        
        # Initialize user achievements if they don't exist
        for achievement_data in ACHIEVEMENTS:
            # Find achievement ID
            cursor.execute(
                "SELECT id FROM achievements WHERE name = ?",
                (achievement_data['name'],)
            )
            achievement_result = cursor.fetchone()
            
            if achievement_result:
                achievement_id = achievement_result[0]
                
                # Check if user already has this achievement
                cursor.execute(
                    """
                    SELECT id FROM user_achievements 
                    WHERE user_id = ? AND achievement_id = ?
                    """,
                    (user_id, achievement_id)
                )
                user_achievement_result = cursor.fetchone()
                
                if not user_achievement_result:
                    # Create user achievement tracking
                    cursor.execute(
                        """
                        INSERT INTO user_achievements (user_id, achievement_id, progress, completed)
                        VALUES (?, ?, 0, 0)
                        """,
                        (user_id, achievement_id)
                    )
        
        # Initialize streaks if they don't exist
        streak_types = ['daily_tasks', 'weekly_goals', 'focused_sessions']
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        for streak_type in streak_types:
            cursor.execute(
                """
                SELECT id FROM streaks 
                WHERE user_id = ? AND streak_type = ?
                """,
                (user_id, streak_type)
            )
            streak_result = cursor.fetchone()
            
            if not streak_result:
                cursor.execute(
                    """
                    INSERT INTO streaks (user_id, streak_type, current_count, longest_count, last_activity_date)
                    VALUES (?, ?, 0, 0, ?)
                    """,
                    (user_id, streak_type, today)
                )
        
        users_initialized += 1
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Initialization completed. Initialized momentum data for {users_initialized} users.")

async def main():
    """Initialize momentum data for all existing users"""
    try:
        await init_all_users_momentum_direct()
    except Exception as e:
        print(f"Error initializing momentum data: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 