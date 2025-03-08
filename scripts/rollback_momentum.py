#!/usr/bin/env python
import asyncio
import sys
import os
import sqlite3
import json
import argparse
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the momentum constants but not any SQLAlchemy models
from app.momentum.momentum import LEVELS

async def reset_user_points(conn, cursor, user_id=None):
    """Reset user points to zero without affecting other momentum data"""
    if user_id:
        cursor.execute(
            """
            UPDATE users
            SET total_points = 0, weekly_points = 0, monthly_points = 0
            WHERE id = ?
            """,
            (user_id,)
        )
        print(f"Reset points for user ID {user_id}")
    else:
        cursor.execute(
            """
            UPDATE users
            SET total_points = 0, weekly_points = 0, monthly_points = 0
            """
        )
        print("Reset points for all users")

async def reset_user_levels(conn, cursor, user_id=None):
    """Reset users to level 1"""
    # Find level 1 ID
    cursor.execute("SELECT id FROM levels WHERE level_number = 1")
    level_1_result = cursor.fetchone()
    
    if not level_1_result:
        print("ERROR: Level 1 not found in the database.")
        return
    
    level_1_id = level_1_result[0]
    
    if user_id:
        cursor.execute(
            """
            UPDATE users
            SET current_level_id = ?
            WHERE id = ?
            """,
            (level_1_id, user_id)
        )
        print(f"Reset level to Level 1 for user ID {user_id}")
    else:
        cursor.execute(
            """
            UPDATE users
            SET current_level_id = ?
            """,
            (level_1_id,)
        )
        print("Reset all users to Level 1")

async def reset_user_achievements(conn, cursor, user_id=None):
    """Reset user achievements progress to zero and mark as not completed"""
    if user_id:
        cursor.execute(
            """
            UPDATE user_achievements
            SET progress = 0, completed = 0
            WHERE user_id = ?
            """,
            (user_id,)
        )
        print(f"Reset achievements for user ID {user_id}")
    else:
        cursor.execute(
            """
            UPDATE user_achievements
            SET progress = 0, completed = 0
            """
        )
        print("Reset achievements for all users")

async def reset_streaks(conn, cursor, user_id=None):
    """Reset user streaks to zero"""
    if user_id:
        cursor.execute(
            """
            UPDATE streaks
            SET current_count = 0, longest_count = 0
            WHERE user_id = ?
            """,
            (user_id,)
        )
        print(f"Reset streaks for user ID {user_id}")
    else:
        cursor.execute(
            """
            UPDATE streaks
            SET current_count = 0, longest_count = 0
            """
        )
        print("Reset streaks for all users")

async def reset_to_default_levels(conn, cursor):
    """Reset levels to match the default LEVELS structure in momentum.py"""
    # First backup the current levels
    cursor.execute("SELECT * FROM levels")
    current_levels = cursor.fetchall()
    backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with open(f"levels_backup_{backup_time}.json", "w") as f:
        json.dump(current_levels, f, indent=2)
    print(f"Levels backup saved to levels_backup_{backup_time}.json")
    
    # Delete all current levels
    cursor.execute("DELETE FROM levels")
    
    # Insert the default levels from momentum.py
    for level_data in LEVELS:
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
    
    print(f"Reset levels to default configuration from momentum.py")

async def purge_momentum_data(conn, cursor, keep_structure=True):
    """
    Completely purge all momentum data
    
    If keep_structure is True, this only deletes the data but keeps the tables
    If keep_structure is False, it drops the momentum-related tables completely
    """
    if not keep_structure:
        # First check if the tables exist
        tables_to_drop = ['levels', 'achievements', 'user_achievements', 'streaks']
        for table in tables_to_drop:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                cursor.execute(f"DROP TABLE {table}")
                print(f"Dropped table {table}")
        
        # Reset user momentum fields
        cursor.execute(
            """
            UPDATE users
            SET total_points = NULL, weekly_points = NULL, monthly_points = NULL, current_level_id = NULL
            """
        )
        print("Reset user momentum fields")
        
    else:
        # Delete all data but keep the tables
        tables_to_clear = ['levels', 'achievements', 'user_achievements', 'streaks']
        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
            print(f"Cleared all data from {table}")
        
        # Reset user momentum fields
        cursor.execute(
            """
            UPDATE users
            SET total_points = 0, weekly_points = 0, monthly_points = 0, current_level_id = NULL
            """
        )
        print("Reset user momentum fields")

async def rollback_momentum(options):
    """Roll back momentum based on selected options"""
    print("Starting momentum rollback...")
    
    # Connect to SQLite database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        if options.backup:
            # Create a backup of all momentum tables
            tables = ['levels', 'achievements', 'user_achievements', 'streaks']
            backup_data = {}
            
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                backup_data[table] = cursor.fetchall()
            
            # Get column names for each table
            cursor.execute("PRAGMA table_info(levels)")
            level_columns = [col[1] for col in cursor.fetchall()]
            
            cursor.execute("PRAGMA table_info(achievements)")
            achievement_columns = [col[1] for col in cursor.fetchall()]
            
            cursor.execute("PRAGMA table_info(user_achievements)")
            user_achievement_columns = [col[1] for col in cursor.fetchall()]
            
            cursor.execute("PRAGMA table_info(streaks)")
            streak_columns = [col[1] for col in cursor.fetchall()]
            
            column_data = {
                'levels': level_columns,
                'achievements': achievement_columns,
                'user_achievements': user_achievement_columns,
                'streaks': streak_columns
            }
            
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"momentum_backup_{backup_time}.json"
            
            with open(backup_file, "w") as f:
                json.dump({
                    'column_data': column_data,
                    'table_data': backup_data
                }, f, indent=2)
            
            print(f"Backup created: {backup_file}")
        
        if options.user_id and len(options.user_id) > 0:
            user_id = options.user_id
            # Verify user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                print(f"ERROR: User ID {user_id} not found in the database.")
                return
        else:
            user_id = None
        
        # Execute the requested operations
        if options.reset_points:
            await reset_user_points(conn, cursor, user_id)
        
        if options.reset_levels:
            await reset_user_levels(conn, cursor, user_id)
        
        if options.reset_achievements:
            await reset_user_achievements(conn, cursor, user_id)
        
        if options.reset_streaks:
            await reset_streaks(conn, cursor, user_id)
        
        if options.reset_default_levels:
            await reset_to_default_levels(conn, cursor)
        
        if options.purge:
            confirm = input("Are you sure you want to completely purge all momentum data? This cannot be undone. (y/n): ")
            if confirm.lower() == 'y':
                await purge_momentum_data(conn, cursor, keep_structure=options.keep_structure)
            else:
                print("Purge operation cancelled.")
        
        # Commit changes
        conn.commit()
        print("Momentum rollback completed successfully.")
        
    except Exception as e:
        print(f"Error during rollback: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

async def main():
    """Parse command line arguments and execute rollback"""
    parser = argparse.ArgumentParser(description='Roll back momentum feature')
    
    parser.add_argument('--backup', action='store_true', 
                      help='Create a backup of all momentum data before making changes')
    
    parser.add_argument('--user-id', type=int,
                      help='Specify a user ID to only affect that user')
    
    parser.add_argument('--reset-points', action='store_true',
                      help='Reset points to zero')
    
    parser.add_argument('--reset-levels', action='store_true',
                      help='Reset users to level 1')
    
    parser.add_argument('--reset-achievements', action='store_true',
                      help='Reset achievement progress to zero')
    
    parser.add_argument('--reset-streaks', action='store_true',
                      help='Reset streaks to zero')
    
    parser.add_argument('--reset-default-levels', action='store_true',
                      help='Reset levels to default configuration from momentum.py')
    
    parser.add_argument('--purge', action='store_true',
                      help='Completely purge all momentum data')
    
    parser.add_argument('--keep-structure', action='store_true',
                      help='When purging, keep table structure but delete all data')
    
    parser.add_argument('--reset-all-users', action='store_true',
                      help='Reset all user momentum progress (points, level, achievements, streaks)')
    
    options = parser.parse_args()
    
    # If reset-all-users is specified, set all the individual reset flags
    if options.reset_all_users:
        options.reset_points = True
        options.reset_levels = True
        options.reset_achievements = True
        options.reset_streaks = True
    
    # If no options were provided, print help
    if not any([
        options.backup,
        options.reset_points,
        options.reset_levels,
        options.reset_achievements,
        options.reset_streaks,
        options.reset_default_levels,
        options.purge,
        options.reset_all_users
    ]):
        parser.print_help()
        print("\nNo operations specified. Please specify at least one operation to perform.")
        return
    
    await rollback_momentum(options)

if __name__ == "__main__":
    asyncio.run(main()) 