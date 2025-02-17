# services.py

from sqlalchemy.orm import Session
import logging
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List, Dict
from .. import models
from . import schemas
from .momentum import POINT_EVENTS, ACHIEVEMENTS, LEVELS, CriteriaType

logger = logging.getLogger(__name__)

class MomentumService:
    def __init__(self, db: Session):
        self.db = db

    async def process_event(self, user_id: int, event_type: str, metadata: Dict = None) -> Dict:
        """Process a momentum event and return updated user stats"""
        metadata = metadata or {}
        points = self._calculate_points(event_type, metadata)
        
        # Award points and update stats
        user_stats = await self.award_points(user_id, points)
        
        # Update streaks
        streak_updates = await self.update_streaks(user_id, event_type)
        
        # Check achievements
        new_achievements = await self.check_achievements(user_id)
        
        # Check for level up
        level_up = await self.check_level_up(user_id)
        
        return {
            "points_awarded": points,
            "user_stats": user_stats,
            "streak_updates": streak_updates,
            "new_achievements": new_achievements,
            "level_up": level_up
        }

    async def award_points(self, user_id: int, points: int) -> Dict:
        """Award points to user and update various point counters"""
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        user.total_points += points
        user.weekly_points += points
        user.monthly_points += points
        
        self.db.commit()
        
        return {
            "total_points": user.total_points,
            "weekly_points": user.weekly_points,
            "monthly_points": user.monthly_points
        }

    async def check_achievements(self, user_id: int) -> List[schemas.Achievement]:
        """Check and award any newly completed achievements"""
        new_achievements = []
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        
        for achievement in ACHIEVEMENTS:
            user_achievement = self.db.query(models.UserAchievement).filter(
                models.UserAchievement.user_id == user_id,
                models.UserAchievement.achievement.has(name=achievement['name'])
            ).first()
            
            if not user_achievement or not user_achievement.completed:
                if await self._check_achievement_criteria(user_id, achievement):
                    new_achievement = await self._award_achievement(user_id, achievement)
                    new_achievements.append(new_achievement)
        
        return new_achievements

    async def update_streaks(self, user_id: int, event_type: str) -> Dict:
        """Update user streaks based on activity"""
        streak = self.db.query(models.Streak).filter(
            models.Streak.user_id == user_id,
            models.Streak.streak_type == event_type
        ).first()
        
        if not streak:
            streak = models.Streak(
                user_id=user_id,
                streak_type=event_type,
                current_count=1,
                longest_count=1,
                last_activity_date=datetime.utcnow().date()
            )
            self.db.add(streak)
        else:
            last_date = streak.last_activity_date
            current_date = datetime.utcnow().date()
            
            if (current_date - last_date).days == 1:
                streak.current_count += 1
                if streak.current_count > streak.longest_count:
                    streak.longest_count = streak.current_count
            elif (current_date - last_date).days > 1:
                streak.current_count = 1
            
            streak.last_activity_date = current_date
        
        self.db.commit()
        return {
            "streak_type": streak.streak_type,
            "current_count": streak.current_count,
            "longest_count": streak.longest_count
        }

    async def check_level_up(self, user_id: int) -> Optional[schemas.Level]:
        """Check if user has leveled up and update if necessary"""
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        current_level = user.current_level
        
        for level in LEVELS:
            if (level['level_number'] > current_level.level_number and 
                user.total_points >= level['points_required']):
                user.current_level_id = level['level_number']
                self.db.commit()
                return schemas.Level.from_orm(user.current_level)
            
    async def get_user_progress(self, user_id: int) -> schemas.UserProgress:
        """Get detailed progress information for a user"""
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        
        # Get next level information
        next_level = self.db.query(models.Level).filter(
            models.Level.points_required > user.total_points
        ).order_by(models.Level.points_required.asc()).first()
        
        # Calculate progress to next level
        points_to_next = next_level.points_required - user.total_points if next_level else 0
        total_points_in_level = (next_level.points_required - user.current_level.points_required) if next_level else 1
        points_earned_in_level = user.total_points - user.current_level.points_required
        completion_percentage = (points_earned_in_level / total_points_in_level) * 100
        
        # Get recent achievements
        recent_achievements = self.db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user_id,
            models.UserAchievement.completed == True
        ).order_by(models.UserAchievement.completed_at.desc()).limit(5).all()
        
        # Get active streaks
        active_streaks = self.db.query(models.Streak).filter(
            models.Streak.user_id == user_id,
            models.Streak.current_count > 0
        ).all()
        
        return schemas.UserProgress(
            current_level=user.current_level,
            total_points=user.total_points,
            points_to_next_level=points_to_next,
            completion_percentage=completion_percentage,
            recent_achievements=recent_achievements,
            active_streaks=active_streaks
        )

    async def get_leaderboard(
        self,
        timeframe: str = "weekly",
        limit: int = 10,
        user_id: Optional[int] = None
    ) -> List[schemas.LeaderboardEntry]:
        """Get leaderboard data with optional user context"""
        if timeframe == "weekly":
            points_column = models.User.weekly_points
        elif timeframe == "monthly":
            points_column = models.User.monthly_points
        else:
            points_column = models.User.total_points
            
        leaderboard = self.db.query(
            models.User.id,
            models.User.username,
            points_column.label('points'),
            models.Level.level_number,
            func.count(models.UserAchievement.id).label('achievements_count'),
            func.max(models.Streak.longest_count).label('longest_streak')
        ).join(
            models.Level,
            models.User.current_level_id == models.Level.id
        ).outerjoin(
            models.UserAchievement,
            models.User.id == models.UserAchievement.user_id
        ).outerjoin(
            models.Streak,
            models.User.id == models.Streak.user_id
        ).group_by(
            models.User.id,
            models.User.username,
            points_column,
            models.Level.level_number
        ).order_by(points_column.desc()).limit(limit).all()
        
        return [schemas.LeaderboardEntry.from_orm(entry) for entry in leaderboard]

    async def get_momentum_stats(self, user_id: int) -> schemas.MomentumStats:
        """Get comprehensive momentum statistics for a user"""
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        
        # Get achievement stats
        total_achievements = self.db.query(func.count(models.UserAchievement.id)).filter(
            models.UserAchievement.user_id == user_id,
            models.UserAchievement.completed == True
        ).scalar()
        
        # Get current streaks
        streaks = self.db.query(models.Streak).filter(
            models.Streak.user_id == user_id
        ).all()
        current_streaks = {streak.streak_type: streak.current_count for streak in streaks}
        
        # Calculate level progress
        next_level = self.db.query(models.Level).filter(
            models.Level.points_required > user.total_points
        ).order_by(models.Level.points_required.asc()).first()
        
        if next_level:
            level_progress = (user.total_points - user.current_level.points_required) / (
                next_level.points_required - user.current_level.points_required
            )
        else:
            level_progress = 1.0
            
        # Get recent awards
        recent_awards = self.db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user_id,
            models.UserAchievement.completed == True
        ).order_by(models.UserAchievement.completed_at.desc()).limit(5).all()
        
        # Get leaderboard position
        leaderboard_position = await self._get_leaderboard_position(user_id)
        
        return schemas.MomentumStats(
            total_achievements=total_achievements,
            total_points=user.total_points,
            current_streaks=current_streaks,
            level_progress=level_progress,
            recent_awards=recent_awards,
            leaderboard_position=leaderboard_position
        )

    async def _get_leaderboard_position(self, user_id: int) -> Optional[int]:
        """Helper method to get user's position on the leaderboard"""
        subquery = self.db.query(
            models.User.id,
            func.rank().over(
                order_by=models.User.total_points.desc()
            ).label('rank')
        ).subquery()
        
        result = self.db.query(subquery.c.rank).filter(
            subquery.c.id == user_id
        ).first()
        
        return result[0] if result else None

    async def _check_achievement_criteria(self, user_id: int, achievement: Dict) -> bool:
        """Helper method to check if achievement criteria are met"""
        if achievement['criteria_type'] == CriteriaType.COUNT:
            return await self._check_count_criteria(user_id, achievement)
        elif achievement['criteria_type'] == CriteriaType.STREAK:
            return await self._check_streak_criteria(user_id, achievement)
        elif achievement['criteria_type'] == CriteriaType.TIME:
            return await self._check_time_criteria(user_id, achievement)
        elif achievement['criteria_type'] == CriteriaType.SPECIFIC_TIME:
            return await self._check_specific_time_criteria(user_id, achievement)
        elif achievement['criteria_type'] == CriteriaType.COMPOUND:
            return await self._check_compound_criteria(user_id, achievement)
        return False
    
    async def _calculate_points(self, event_type: str, metadata: Dict) -> int:
        """
        Calculate points for a given event type with metadata
        Returns the total points earned for the event
        """
        base_points = POINT_EVENTS.get(event_type, 0)
        
        # If points is a callable (lambda function), execute it with metadata
        if callable(base_points):
            try:
                if event_type == 'focused_session':
                    points = base_points(metadata.get('duration', 0))
                elif event_type == 'streak_milestone':
                    points = base_points(metadata.get('streak', 1))
                elif event_type == 'goal_streak':
                    points = base_points(metadata.get('streak', 1))
                elif event_type == 'task_complexity':
                    points = base_points(metadata.get('complexity', 1))
                else:
                    points = base_points(1)  # Default multiplier
            except Exception as e:
                logger.error(f"Error calculating points for {event_type}: {str(e)}")
                points = 0
        else:
            points = base_points

        # Apply any bonus multipliers
        multiplier = 1.0

        # Weekend bonus (if applicable)
        if metadata.get('is_weekend'):
            multiplier *= 1.2

        # First task of the day bonus
        if metadata.get('is_first_task'):
            multiplier *= 1.1

        # Streak bonus (increases with streak length)
        if streak_length := metadata.get('current_streak', 0):
            # Cap the streak multiplier at 2.0 (achieved at 20-day streak)
            streak_bonus = min(1 + (streak_length * 0.05), 2.0)
            multiplier *= streak_bonus

        # Apply time-based bonuses
        if completion_time := metadata.get('completion_time'):
            hour = completion_time.hour
            # Early bird bonus (before 9 AM)
            if 5 <= hour < 9:
                multiplier *= 1.15
            # Night owl bonus (after 9 PM)
            elif 21 <= hour < 24:
                multiplier *= 1.15

        # Special event bonus (if any active)
        if metadata.get('special_event_multiplier'):
            multiplier *= metadata.get('special_event_multiplier')

        # Calculate final points with multiplier
        final_points = int(points * multiplier)

        # Log point calculation for debugging
        logger.debug(
            f"Point calculation: {event_type} - Base: {points}, "
            f"Multiplier: {multiplier}, Final: {final_points}"
        )

        return final_points

    async def calculate_streak_bonus(self, streak_length: int) -> float:
        """
        Calculate bonus multiplier based on streak length
        Returns a multiplier between 1.0 and 2.0
        """
        return min(1 + (streak_length * 0.05), 2.0)

    async def calculate_time_bonus(self, completion_time: datetime) -> float:
        """
        Calculate time-based bonus multiplier
        Returns 1.15 for early bird or night owl, 1.0 otherwise
        """
        hour = completion_time.hour
        if 5 <= hour < 9 or 21 <= hour < 24:
            return 1.15
        return 1.0
    
    async def get_levels(self) -> List[schemas.Level]:
        """Retrieve all levels and their requirements."""
        # Simulate fetching data from the LEVELS constant.
        levels = [
            schemas.Level(
                id=index + 1,  # Assigning a unique ID to each level
                level_number=level['level_number'],
                points_required=level['points_required'],
                title=level['title'],
                perks=level['perks']
            )
            for index, level in enumerate(LEVELS)
        ]
        return levels
    
    async def get_available_achievements(self, category: Optional[schemas.AchievementCategory] = None) -> List[schemas.Achievement]:
        """
        Retrieve achievements, optionally filtered by category.

        :param category: Optional category to filter achievements.
        :return: List of achievements matching the filter.
        """
        # Filter achievements by category if provided
        filtered_achievements = [
            schemas.Achievement(
                id=index + 1,  # Assign unique ID to each achievement
                name=achievement['name'],
                description=achievement['description'],
                points=achievement['points'],
                category=achievement['category'],
                criteria_type=achievement['criteria_type'],
                criteria_value=achievement['criteria_value'],
                icon_name=achievement['icon_name'],
            )
            for index, achievement in enumerate(ACHIEVEMENTS)
            if category is None or achievement['category'] == category
        ]
        return filtered_achievements