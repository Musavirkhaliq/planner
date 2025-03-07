-- SQL Statements to Upgrade Database from V1 to V2

-- Add missing columns to users table
ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'Asia/Kolkata';
ALTER TABLE users ADD COLUMN current_level_id INTEGER REFERENCES levels(id);
ALTER TABLE users ADD COLUMN total_points INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN weekly_points INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN monthly_points INTEGER DEFAULT 0;

-- Create achievements table
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    description TEXT,
    points INTEGER DEFAULT 0,
    category TEXT,
    criteria_type TEXT,
    criteria_value INTEGER,
    icon_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create user_achievements table
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    achievement_id INTEGER REFERENCES achievements(id),
    progress INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    completed_at DATETIME
);

-- Create streaks table
CREATE TABLE IF NOT EXISTS streaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    streak_type TEXT,
    current_count INTEGER DEFAULT 0,
    longest_count INTEGER DEFAULT 0,
    last_activity_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create levels table
CREATE TABLE IF NOT EXISTS levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_number INTEGER UNIQUE NOT NULL,
    points_required INTEGER NOT NULL,
    title TEXT NOT NULL,
    perks TEXT NOT NULL DEFAULT '{"can_create_goals":true,"can_track_time":true,"can_earn_achievements":true,"can_view_analytics":true}'
);
