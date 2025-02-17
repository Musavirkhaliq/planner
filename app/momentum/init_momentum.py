from sqlalchemy.orm import Session
from .. import models
from .momentum import LEVELS, ACHIEVEMENTS
from datetime import datetime
from ..json_utils import serialize_json

async def init_user_momentum(db: Session, user_id: int):
    """Initialize momentum data for an existing user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return
        
    # Initialize points if not set
    if user.total_points is None:
        user.total_points = 0
    if user.weekly_points is None:
        user.weekly_points = 0
    if user.monthly_points is None:
        user.monthly_points = 0
        
    # Initialize level if not set
    if not user.current_level_id:
        level_1 = db.query(models.Level).filter(models.Level.level_number == 1).first()
        if not level_1:
            # Create level 1 if it doesn't exist
            perks = {
                "can_create_goals": True,
                "can_track_time": True,
                "can_earn_achievements": True,
                "can_view_analytics": True
            }
            level_1 = models.Level(
                level_number=1,
                points_required=0,
                title=LEVELS[0]['title'],
                perks=serialize_json(perks)
            )
            db.add(level_1)
            db.commit()
            db.refresh(level_1)
        
        user.current_level_id = level_1.id
        db.commit()
        
    # Initialize all levels if they don't exist
    for level_data in LEVELS:
        level = db.query(models.Level).filter(
            models.Level.level_number == level_data['level_number']
        ).first()
        
        if not level:
            level = models.Level(
                level_number=level_data['level_number'],
                points_required=level_data['points_required'],
                title=level_data['title'],
                perks=serialize_json(level_data['perks'])
            )
            db.add(level)
            
    db.commit()
            
    # Initialize achievements
    for achievement_data in ACHIEVEMENTS:
        achievement = db.query(models.Achievement).filter(
            models.Achievement.name == achievement_data['name']
        ).first()
        
        if not achievement:
            achievement = models.Achievement(
                name=achievement_data['name'],
                description=achievement_data['description'],
                points=achievement_data['points'],
                category=achievement_data['category'],
                criteria_type=achievement_data['criteria_type'],
                criteria_value=achievement_data['criteria_value'],
                icon_name=achievement_data['icon_name']
            )
            db.add(achievement)
            db.commit()
            db.refresh(achievement)
            
        # Create user achievement tracking if not exists
        user_achievement = db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user_id,
            models.UserAchievement.achievement_id == achievement.id
        ).first()
        
        if not user_achievement:
            user_achievement = models.UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                progress=0,
                completed=False
            )
            db.add(user_achievement)
            
    # Initialize streaks
    streak_types = ['daily_tasks', 'weekly_goals', 'focused_sessions']
    for streak_type in streak_types:
        streak = db.query(models.Streak).filter(
            models.Streak.user_id == user_id,
            models.Streak.streak_type == streak_type
        ).first()
        
        if not streak:
            streak = models.Streak(
                user_id=user_id,
                streak_type=streak_type,
                current_count=0,
                longest_count=0,
                last_activity_date=datetime.utcnow().date()
            )
            db.add(streak)
            
    db.commit()

async def init_all_users_momentum(db: Session):
    """Initialize momentum data for all existing users"""
    users = db.query(models.User).all()
    for user in users:
        await init_user_momentum(db, user.id) 