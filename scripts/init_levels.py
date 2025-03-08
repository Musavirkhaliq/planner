#!/usr/bin/env python
import asyncio
import sys
import os
import sqlite3
import json

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.momentum.momentum import LEVELS

async def init_all_levels():
    """Initialize all levels from the LEVELS list in momentum.py directly using SQLite"""
    print("Initializing all levels from momentum.py...")
    
    # Connect to SQLite database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_created = 0
    total_updated = 0
    
    for level_data in LEVELS:
        # Check if level exists
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
            total_created += 1
        else:
            # Update existing level
            cursor.execute(
                """
                UPDATE levels 
                SET points_required = ?, title = ?, perks = ? 
                WHERE level_number = ?
                """, 
                (
                    level_data['points_required'], 
                    level_data['title'], 
                    json.dumps(level_data['perks']),
                    level_data['level_number']
                )
            )
            total_updated += 1
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Initialization completed. Created {total_created} new levels, updated {total_updated} existing levels.")

async def main():
    """Initialize all levels from the LEVELS list in momentum.py"""
    try:
        await init_all_levels()
    except Exception as e:
        print(f"Error initializing levels: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 