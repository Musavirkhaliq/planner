# services.py

from sqlalchemy.orm import Session
import logging
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from .. import models
from . import schemas
from .momentum import POINT_EVENTS, ACHIEVEMENTS, LEVELS, CriteriaType
import json

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

    async def revert_event(self, user_id: int, event_type: str, metadata: Dict = None) -> Dict:
        """
        Revert a momentum event (e.g., when a completed task or time slot is uncompleted or deleted)
        This removes the points that were previously awarded for the event
        """
        metadata = metadata or {}
        points = self._calculate_points(event_type, metadata)
        
        # Deduct points 
        user_stats = await self.deduct_points(user_id, points)
        
        # We don't revert streaks as that would be complex and potentially confusing to users
        # Instead we simply stop incrementing them on future events if the streak is broken
        
        return {
            "points_deducted": points,
            "user_stats": user_stats,
            "message": f"Reverted {event_type} event, deducted {points} points"
        }

    async def deduct_points(self, user_id: int, points: int) -> Dict:
        """Deduct points from user's various point counters, ensuring they don't go below zero"""
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        
        # Deduct points, ensuring we don't go below zero
        user.total_points = max(0, user.total_points - points)
        user.weekly_points = max(0, user.weekly_points - points)
        user.monthly_points = max(0, user.monthly_points - points)
        
        # Check if level should be adjusted
        current_level = user.current_level
        if current_level and current_level.level_number > 1:
            # Get previous level
            previous_level = self.db.query(models.Level).filter(
                models.Level.level_number == current_level.level_number - 1
            ).first()
            
            # If user's points are now below current level requirement, demote them
            if user.total_points < current_level.points_required and previous_level:
                user.current_level_id = previous_level.id
        
        self.db.commit()
        
        return {
            "total_points": user.total_points,
            "weekly_points": user.weekly_points,
            "monthly_points": user.monthly_points,
            "current_level": user.current_level.level_number if user.current_level else 1
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
        
        # Initialize user's level if not set
        if not user.current_level_id or not user.current_level:
            level_1 = self.db.query(models.Level).filter(
                models.Level.level_number == 1
            ).first()
            
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
                    perks=json.dumps(perks)
                )
                self.db.add(level_1)
                self.db.commit()
                self.db.refresh(level_1)
            
            user.current_level_id = level_1.id
            self.db.commit()
            self.db.refresh(user)
        
        current_level = user.current_level
        if not current_level:
            logger.error(f"Failed to initialize current_level for user {user_id}")
            return None
        
        for level in LEVELS:
            if (level['level_number'] > current_level.level_number and 
                user.total_points >= level['points_required']):
                # Get or create the level in the database
                db_level = self.db.query(models.Level).filter(
                    models.Level.level_number == level['level_number']
                ).first()
                
                if not db_level:
                    db_level = models.Level(
                        level_number=level['level_number'],
                        points_required=level['points_required'],
                        title=level['title'],
                        perks=json.dumps(level['perks'])
                    )
                    self.db.add(db_level)
                    self.db.commit()
                    self.db.refresh(db_level)
                
                user.current_level_id = db_level.id
                self.db.commit()
                self.db.refresh(user)
                
                # Ensure perks is properly formatted before conversion
                if isinstance(db_level.perks, str):
                    try:
                        db_level.perks = json.loads(db_level.perks)
                    except json.JSONDecodeError:
                        db_level.perks = {
                            "can_create_goals": True,
                            "can_track_time": True,
                            "can_earn_achievements": True,
                            "can_view_analytics": True
                        }
                elif db_level.perks is None:
                    db_level.perks = {
                        "can_create_goals": True,
                        "can_track_time": True,
                        "can_earn_achievements": True,
                        "can_view_analytics": True
                    }
                
                return schemas.Level(
                    id=db_level.id,
                    level_number=db_level.level_number,
                    points_required=db_level.points_required,
                    title=db_level.title,
                    perks=db_level.perks
                )
        return None

    async def get_user_progress(self, user_id: int) -> schemas.UserProgress:
        """Get detailed progress information for a user"""
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        
        # Handle case when user is not found
        if user is None:
            beginner_level = schemas.Level(
                id=1, 
                level_number=1,
                points_required=0,
                title="Beginner",
                perks={
                    "can_create_goals": True,
                    "can_track_time": True,
                    "can_earn_achievements": True,
                    "can_view_analytics": True
                }
            )
            
            intermediate_level = schemas.Level(
                id=2, 
                level_number=2,
                points_required=101,
                title="Intermediate",
                perks={
                    "can_create_goals": True,
                    "can_track_time": True,
                    "can_earn_achievements": True,
                    "can_view_analytics": True
                }
            )
            
            return schemas.UserProgress(
                current_level=beginner_level,
                next_level=intermediate_level,
                total_points=0,
                points_to_next_level=100,
                completion_percentage=0.0,
                recent_achievements=[],
                active_streaks=[]
            )

        # Initialize user's points if not set
        if user.total_points is None:
            user.total_points = 0
            user.weekly_points = 0
            user.monthly_points = 0
        
        # Initialize user's level if not set
        if not user.current_level_id:
            level_1 = self.db.query(models.Level).filter(
                models.Level.level_number == 1
            ).first()
            
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
                    perks=json.dumps(perks)  # Serialize perks to JSON string
                )
                self.db.add(level_1)
                self.db.commit()
                self.db.refresh(level_1)
            
            user.current_level_id = level_1.id
            self.db.commit()
            self.db.refresh(user)
        
        # Ensure current level perks is properly formatted
        current_level = user.current_level
        if current_level.perks is None:
            current_level.perks = json.dumps({
                "can_create_goals": True,
                "can_track_time": True,
                "can_earn_achievements": True,
                "can_view_analytics": True
            })
            self.db.commit()
        
        # Convert perks from JSON string to dict if needed
        if isinstance(current_level.perks, str):
            try:
                perks_dict = json.loads(current_level.perks)
            except json.JSONDecodeError:
                perks_dict = {
                    "can_create_goals": True,
                    "can_track_time": True,
                    "can_earn_achievements": True,
                    "can_view_analytics": True
                }
        else:
            perks_dict = current_level.perks or {
                "can_create_goals": True,
                "can_track_time": True,
                "can_earn_achievements": True,
                "can_view_analytics": True
            }
        
        # Get next level information
        next_level = self.db.query(models.Level).filter(
            models.Level.points_required > user.total_points
        ).order_by(models.Level.points_required.asc()).first()
        
        # Calculate progress to next level
        points_to_next = next_level.points_required - user.total_points if next_level else 0
        total_points_in_level = (next_level.points_required - current_level.points_required) if next_level else 1
        points_earned_in_level = user.total_points - current_level.points_required
        completion_percentage = (points_earned_in_level / total_points_in_level) * 100 if total_points_in_level > 0 else 100
        
        # Get recent achievements
        recent_achievements = self.db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user_id,
            models.UserAchievement.completed == True
        ).order_by(models.UserAchievement.completed_at.desc()).limit(5).all()
        
        # Initialize achievements if none exist
        if not recent_achievements:
            await self.get_user_achievements(user_id)
            recent_achievements = []
        
        # Get active streaks
        active_streaks = self.db.query(models.Streak).filter(
            models.Streak.user_id == user_id,
            models.Streak.current_count > 0
        ).all()
        
        # Initialize streaks if none exist
        if not active_streaks:
            await self.get_user_streaks(user_id)
            active_streaks = []
        
        # Create Level model with properly formatted data
        level_model = schemas.Level(
            id=current_level.id,
            level_number=current_level.level_number,
            points_required=current_level.points_required,
            title=current_level.title,
            perks=perks_dict
        )
        
        # Create Next Level model if available
        next_level_model = None
        if next_level:
            if isinstance(next_level.perks, str):
                try:
                    next_perks_dict = json.loads(next_level.perks)
                except json.JSONDecodeError:
                    next_perks_dict = perks_dict.copy()
            else:
                next_perks_dict = next_level.perks or perks_dict.copy()
            
            next_level_model = schemas.Level(
                id=next_level.id,
                level_number=next_level.level_number,
                points_required=next_level.points_required,
                title=next_level.title,
                perks=next_perks_dict
            )
        
        return schemas.UserProgress(
            current_level=level_model,
            next_level=next_level_model,
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
            models.User.id.label('user_id'),
            models.User.username,
            points_column.label('points'),
            models.Level.level_number.label('level'),
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
        
        # Convert SQLAlchemy Row objects to dictionaries with proper field names
        leaderboard_entries = []
        for entry in leaderboard:
            entry_dict = {
                'user_id': entry.user_id,
                'username': entry.username,
                'points': entry.points or 0,  # Handle None values
                'level': entry.level,
                'achievements_count': entry.achievements_count or 0,
                'longest_streak': entry.longest_streak or 0
            }
            leaderboard_entries.append(schemas.LeaderboardEntry(**entry_dict))
        
        return leaderboard_entries

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
    
    def _calculate_points(self, event_type: str, metadata: Dict) -> int:
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
            multiplier *= 1.1  # Reduced from 1.2

        # First task of the day bonus
        if metadata.get('is_first_task'):
            multiplier *= 1.05  # Reduced from 1.1

        # Streak bonus (increases with streak length)
        if streak_length := metadata.get('current_streak', 0):
            # Cap the streak multiplier at 1.5 (achieved at 25-day streak)
            streak_bonus = min(1 + (streak_length * 0.02), 1.5)  # Reduced from 0.05 and max 2.0
            multiplier *= streak_bonus

        # Apply time-based bonuses
        if completion_time := metadata.get('completion_time'):
            hour = completion_time.hour
            # Early bird bonus (before 9 AM)
            if 5 <= hour < 9:
                multiplier *= 1.07  # Reduced from 1.15
            # Night owl bonus (after 9 PM)
            elif 21 <= hour < 24:
                multiplier *= 1.07  # Reduced from 1.15

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

    async def _check_count_criteria(self, user_id: int, achievement: Dict) -> bool:
        """Check if count-based achievement criteria are met"""
        if achievement['category'] == 'productivity':
            count = self.db.query(models.Task).filter(
                models.Task.owner_id == user_id,
                models.Task.completed == True
            ).count()
        elif achievement['category'] == 'time_management':
            count = self.db.query(models.TimeSlot).filter(
                models.TimeSlot.owner_id == user_id,
                models.TimeSlot.status == 'completed'
            ).count()
        else:
            count = 0
        return count >= achievement['criteria_value']

    async def _check_streak_criteria(self, user_id: int, achievement: Dict) -> bool:
        """Check if streak-based achievement criteria are met"""
        streak = self.db.query(models.Streak).filter(
            models.Streak.user_id == user_id,
            models.Streak.streak_type == achievement['name'].lower()
        ).first()
        
        if not streak:
            return False
            
        return streak.longest_count >= achievement['criteria_value']

    async def _check_time_criteria(self, user_id: int, achievement: Dict) -> bool:
        """Check if time-based achievement criteria are met"""
        total_time = self.db.query(func.sum(models.Task.time_spent)).filter(
            models.Task.owner_id == user_id,
            models.Task.completed == True
        ).scalar() or 0
        
        return total_time >= achievement['criteria_value']

    async def _check_specific_time_criteria(self, user_id: int, achievement: Dict) -> bool:
        """Check if specific time-based achievement criteria are met"""
        if achievement['name'] == 'Early Riser':
            count = self.db.query(models.Task).filter(
                models.Task.owner_id == user_id,
                models.Task.completed == True,
                func.extract('hour', models.Task.created_at) < 9
            ).count()
            return count >= achievement['criteria_value']
        return False

    async def _check_compound_criteria(self, user_id: int, achievement: Dict) -> bool:
        """Check if compound achievement criteria are met"""
        if achievement['name'] == 'Goal Strategist':
            # Count goals with 5+ steps that are completed
            complex_goals = self.db.query(models.Goal).filter(
                models.Goal.owner_id == user_id,
                models.Goal.completed == True
            ).join(models.GoalStep).group_by(models.Goal.id).having(
                func.count(models.GoalStep.id) >= 5
            ).count()
            return complex_goals >= achievement['criteria_value']
            
        elif achievement['name'] == 'Productivity Pioneer':
            # Check if user has used all features in a week
            week_ago = datetime.utcnow() - timedelta(days=7)
            has_tasks = self.db.query(models.Task).filter(
                models.Task.owner_id == user_id,
                models.Task.created_at >= week_ago
            ).first() is not None
            
            has_goals = self.db.query(models.Goal).filter(
                models.Goal.owner_id == user_id,
                models.Goal.created_at >= week_ago
            ).first() is not None
            
            has_time_slots = self.db.query(models.TimeSlot).filter(
                models.TimeSlot.owner_id == user_id,
                models.TimeSlot.created_at >= week_ago
            ).first() is not None
            
            return has_tasks and has_goals and has_time_slots
            
        elif achievement['name'] == 'Leaderboard Legend':
            # Check if user is #1 on weekly leaderboard
            top_user = self.db.query(models.User).order_by(
                models.User.weekly_points.desc()
            ).first()
            return top_user and top_user.id == user_id
            
        return False

    async def _award_achievement(self, user_id: int, achievement: Dict) -> schemas.Achievement:
        """Award an achievement to a user"""
        # Get or create achievement record
        db_achievement = self.db.query(models.Achievement).filter(
            models.Achievement.name == achievement['name']
        ).first()
        
        if not db_achievement:
            db_achievement = models.Achievement(
                name=achievement['name'],
                description=achievement['description'],
                points=achievement['points'],
                category=achievement['category'],
                criteria_type=achievement['criteria_type'],
                criteria_value=achievement['criteria_value'],
                icon_name=achievement['icon_name']
            )
            self.db.add(db_achievement)
            self.db.commit()
            self.db.refresh(db_achievement)
        
        # Create user achievement record
        user_achievement = models.UserAchievement(
            user_id=user_id,
            achievement_id=db_achievement.id,
            progress=achievement['criteria_value'],
            completed=True,
            completed_at=datetime.utcnow()
        )
        self.db.add(user_achievement)
        
        # Award points to user
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        user.total_points += achievement['points']
        user.weekly_points += achievement['points']
        user.monthly_points += achievement['points']
        
        self.db.commit()
        self.db.refresh(user_achievement)
        
        return schemas.Achievement.from_orm(db_achievement)

    async def get_user_streaks(self, user_id: int) -> List[schemas.Streak]:
        """Get all active streaks for a user"""
        streaks = self.db.query(models.Streak).filter(
            models.Streak.user_id == user_id
        ).all()
        
        if not streaks:
            # Initialize default streaks if none exist
            default_streak_types = ['daily_tasks', 'weekly_goals', 'focused_sessions']
            streaks = []
            
            for streak_type in default_streak_types:
                streak = models.Streak(
                    user_id=user_id,
                    streak_type=streak_type,
                    current_count=0,
                    longest_count=0,
                    last_activity_date=datetime.utcnow().date()
                )
                self.db.add(streak)
                streaks.append(streak)
            
            self.db.commit()
            for streak in streaks:
                self.db.refresh(streak)
        
        return [schemas.Streak.from_orm(streak) for streak in streaks]

    async def get_user_achievements(self, user_id: int) -> List[schemas.UserAchievement]:
        """Get all achievements and their status for a user"""
        # First, ensure all achievements exist in the database
        for achievement_data in ACHIEVEMENTS:
            achievement = self.db.query(models.Achievement).filter(
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
                self.db.add(achievement)
                self.db.commit()
                self.db.refresh(achievement)
            
            # Create user achievement tracking if not exists
            user_achievement = self.db.query(models.UserAchievement).filter(
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
                self.db.add(user_achievement)
        
        self.db.commit()
        
        # Get all user achievements with their related achievement data
        user_achievements = self.db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user_id
        ).join(
            models.Achievement
        ).all()
        
        return [schemas.UserAchievement.from_orm(ua) for ua in user_achievements]

    async def check_perfect_week(self, user_id: int) -> bool:
        """
        Check if a user has completed all their planned tasks for the week
        Returns True if they've achieved a perfect week
        """
        # Get the start of the current week (Monday)
        today = datetime.utcnow().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Get all tasks due this week
        weekly_tasks = self.db.query(models.Task).filter(
            models.Task.owner_id == user_id,
            models.Task.due_date >= start_of_week,
            models.Task.due_date <= end_of_week
        ).all()
        
        # If no tasks were planned, no perfect week
        if not weekly_tasks or len(weekly_tasks) < 3:  # Require at least 3 tasks to get perfect week
            return False
        
        # Check if all tasks were completed
        incomplete_tasks = [task for task in weekly_tasks if not task.completed]
        
        # Perfect week if all tasks were completed
        is_perfect = len(incomplete_tasks) == 0
        
        if is_perfect:
            # Check if we've already awarded perfect week this week
            last_perfect_week = self.db.query(models.MomentumEvent).filter(
                models.MomentumEvent.user_id == user_id,
                models.MomentumEvent.event_type == 'perfect_week',
                models.MomentumEvent.timestamp >= start_of_week
            ).first()
            
            if not last_perfect_week:
                # Award perfect week points
                await self.process_event(
                    user_id=user_id,
                    event_type='perfect_week',
                    metadata={
                        'completion_time': datetime.utcnow(),
                        'week_start': start_of_week.isoformat(),
                        'week_end': end_of_week.isoformat()
                    }
                )
                return True
        
        return False

    async def check_perfect_month(self, user_id: int) -> bool:
        """
        Check if a user has completed all their planned tasks for the month
        Returns True if they've achieved a perfect month
        """
        # Get the start of the current month
        today = datetime.utcnow().date()
        start_of_month = today.replace(day=1)
        
        # Get the end of the month (start of next month - 1 day)
        if today.month == 12:
            end_of_month = datetime(today.year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_of_month = datetime(today.year, today.month + 1, 1).date() - timedelta(days=1)
        
        # Get all tasks due this month
        monthly_tasks = self.db.query(models.Task).filter(
            models.Task.owner_id == user_id,
            models.Task.due_date >= start_of_month,
            models.Task.due_date <= end_of_month
        ).all()
        
        # If no tasks were planned, no perfect month
        if not monthly_tasks or len(monthly_tasks) < 10:  # Require at least 10 tasks to get perfect month
            return False
        
        # Check if all tasks were completed
        incomplete_tasks = [task for task in monthly_tasks if not task.completed]
        
        # Perfect month if all tasks were completed
        is_perfect = len(incomplete_tasks) == 0
        
        if is_perfect:
            # Check if we've already awarded perfect month this month
            last_perfect_month = self.db.query(models.MomentumEvent).filter(
                models.MomentumEvent.user_id == user_id,
                models.MomentumEvent.event_type == 'perfect_month',
                models.MomentumEvent.timestamp >= start_of_month
            ).first()
            
            if not last_perfect_month:
                # Award perfect month points
                await self.process_event(
                    user_id=user_id,
                    event_type='perfect_month',
                    metadata={
                        'completion_time': datetime.utcnow(),
                        'month_start': start_of_month.isoformat(),
                        'month_end': end_of_month.isoformat()
                    }
                )
                return True
        
        return False

    async def schedule_weekly_and_monthly_checks(self):
        """
        Run weekly and monthly checks for all users
        This method should be scheduled to run once a day
        """
        # Get all active users
        users = self.db.query(models.User).filter(models.User.is_active == True).all()
        
        today = datetime.utcnow().date()
        
        for user in users:
            # If today is Sunday, check for perfect week
            if today.weekday() == 6:  # Sunday is 6
                await self.check_perfect_week(user.id)
            
            # If today is the last day of the month, check for perfect month
            tomorrow = today + timedelta(days=1)
            if tomorrow.day == 1:  # Tomorrow is the first day of a new month
                await self.check_perfect_month(user.id)
            
            # Reset points if needed
            await self.reset_periodic_points(user.id)
    
    async def reset_periodic_points(self, user_id: int):
        """
        Reset weekly and monthly points when appropriate
        """
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return
        
        today = datetime.utcnow().date()
        
        # Reset weekly points on Monday
        if today.weekday() == 0:  # Monday is 0
            user.weekly_points = 0
        
        # Reset monthly points on the first day of the month
        if today.day == 1:
            user.monthly_points = 0
        
        self.db.commit()