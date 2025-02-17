# schemas.py

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, date
from .momentum import AchievementCategory, CriteriaType

class AchievementBase(BaseModel):
    name: str
    description: str
    points: int
    category: AchievementCategory
    criteria_type: CriteriaType
    criteria_value: int
    icon_name: str

class AchievementCreate(AchievementBase):
    pass

class Achievement(AchievementBase):
    id: int

    class Config:
        from_attributes = True

class UserAchievementBase(BaseModel):
    progress: int
    completed: bool
    completed_at: Optional[datetime]

class UserAchievement(UserAchievementBase):
    id: int
    user_id: int
    achievement_id: int
    achievement: Achievement

    class Config:
        from_attributes = True

class StreakBase(BaseModel):
    streak_type: str
    current_count: int
    longest_count: int
    last_activity_date: date

class Streak(StreakBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class LevelBase(BaseModel):
    level_number: int
    points_required: int
    title: str
    perks: Dict[str, bool]

class Level(LevelBase):
    id: int

    class Config:
        from_attributes = True

class UserProgress(BaseModel):
    current_level: Level
    total_points: int
    points_to_next_level: int
    completion_percentage: float
    recent_achievements: List[UserAchievement]
    active_streaks: List[Streak]

class LeaderboardEntry(BaseModel):
    user_id: int
    username: str
    points: int
    level: int
    achievements_count: int
    longest_streak: int

class MomentumStats(BaseModel):
    total_achievements: int
    total_points: int
    current_streaks: Dict[str, int]
    level_progress: float
    recent_awards: List[UserAchievement]
    leaderboard_position: Optional[int]