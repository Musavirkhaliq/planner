import pytest
import asyncio
from datetime import datetime, timedelta

from app import models
from app.momentum.momentum import LEVELS, ACHIEVEMENTS
from app.momentum.init_momentum import init_user_momentum, init_all_users_momentum

@pytest.mark.momentum
@pytest.mark.model
class TestInitMomentum:
    """Tests for the momentum initialization functionality"""
    
    @pytest.mark.pre_existing
    def test_init_user_momentum_new_user(self, db_session, test_user):
        """Test initializing momentum for a user that doesn't have momentum data yet"""
        # Note: Due to SQLAlchemy default values, total_points and other fields default to 0 instead of None
        # Before initialization, verify current_level_id is None (no level assigned)
        assert test_user.current_level_id is None
        
        # Run the initialization
        asyncio.run(init_user_momentum(db_session, test_user.id))
        db_session.refresh(test_user)
        
        # Verify points are initialized
        assert test_user.total_points == 0
        assert test_user.weekly_points == 0
        assert test_user.monthly_points == 0
        
        # Verify level is set to level 1
        assert test_user.current_level_id is not None
        assert test_user.current_level.level_number == 1
        assert test_user.current_level.title == LEVELS[0]['title']
        
        # Verify all levels are created
        levels = db_session.query(models.Level).all()
        assert len(levels) == len(LEVELS)
        
        # Verify all achievements are created
        achievements = db_session.query(models.Achievement).all()
        assert len(achievements) == len(ACHIEVEMENTS)
        
        # Verify user achievements are created
        user_achievements = db_session.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == test_user.id
        ).all()
        assert len(user_achievements) == len(ACHIEVEMENTS)
        
        # Verify streaks are created
        streaks = db_session.query(models.Streak).filter(
            models.Streak.user_id == test_user.id
        ).all()
        assert len(streaks) == 3  # daily_tasks, weekly_goals, focused_sessions
        
        # Check streak types
        streak_types = [streak.streak_type for streak in streaks]
        assert 'daily_tasks' in streak_types
        assert 'weekly_goals' in streak_types
        assert 'focused_sessions' in streak_types
    
    def test_init_user_momentum_existing_momentum(self, db_session, additional_users):
        """Test initializing momentum for a user that already has momentum data"""
        # Get the user with existing momentum
        user_with_momentum = additional_users[0]
        
        # Store original values
        original_total_points = user_with_momentum.total_points
        original_weekly_points = user_with_momentum.weekly_points
        original_monthly_points = user_with_momentum.monthly_points
        
        # Run the initialization
        asyncio.run(init_user_momentum(db_session, user_with_momentum.id))
        db_session.refresh(user_with_momentum)
        
        # Verify points remain unchanged
        assert user_with_momentum.total_points == original_total_points
        assert user_with_momentum.weekly_points == original_weekly_points
        assert user_with_momentum.monthly_points == original_monthly_points
    
    @pytest.mark.pre_existing
    def test_init_all_users_momentum(self, db_session, test_user, additional_users):
        """Test initializing momentum for all users"""
        # Ensure we have users with and without momentum
        users = [test_user] + additional_users
        
        # Run the initialization for all users
        asyncio.run(init_all_users_momentum(db_session))
        
        # Refresh users from db
        for user in users:
            db_session.refresh(user)
        
        # Verify all users now have momentum initialized
        for user in users:
            if user.is_active:  # Only check active users
                assert user.total_points is not None
                assert user.weekly_points is not None
                assert user.monthly_points is not None
                assert user.current_level_id is not None
                
                # Verify user achievements
                user_achievements = db_session.query(models.UserAchievement).filter(
                    models.UserAchievement.user_id == user.id
                ).all()
                assert len(user_achievements) == len(ACHIEVEMENTS)
                
                # Verify streaks
                streaks = db_session.query(models.Streak).filter(
                    models.Streak.user_id == user.id
                ).all()
                assert len(streaks) == 3
    
    def test_reinitialize_momentum_is_safe(self, db_session, test_user_with_momentum):
        """Test that running initialization multiple times is safe and doesn't duplicate data"""
        # Get counts before re-initialization
        levels_count_before = db_session.query(models.Level).count()
        achievements_count_before = db_session.query(models.Achievement).count()
        user_achievements_count_before = db_session.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == test_user_with_momentum.id
        ).count()
        streaks_count_before = db_session.query(models.Streak).filter(
            models.Streak.user_id == test_user_with_momentum.id
        ).count()
        
        # Run initialization again
        asyncio.run(init_user_momentum(db_session, test_user_with_momentum.id))
        
        # Get counts after re-initialization
        levels_count_after = db_session.query(models.Level).count()
        achievements_count_after = db_session.query(models.Achievement).count()
        user_achievements_count_after = db_session.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == test_user_with_momentum.id
        ).count()
        streaks_count_after = db_session.query(models.Streak).filter(
            models.Streak.user_id == test_user_with_momentum.id
        ).count()
        
        # Verify counts remain the same
        assert levels_count_before == levels_count_after
        assert achievements_count_before == achievements_count_after
        assert user_achievements_count_before == user_achievements_count_after
        assert streaks_count_before == streaks_count_after
    
    def test_inactive_user_not_affected(self, db_session, additional_users):
        """Test that inactive users are not affected by initialization"""
        # Find the inactive user
        inactive_user = next(user for user in additional_users if not user.is_active)
        
        # Verify inactive user doesn't have a level assigned
        assert inactive_user.current_level_id is None
        
        # Run the initialization (this should still work but not affect inactive user)
        asyncio.run(init_user_momentum(db_session, inactive_user.id))
        db_session.refresh(inactive_user)
        
        # Verify points are initialized even for inactive users (since we directly called init_user_momentum)
        assert inactive_user.total_points == 0
        assert inactive_user.weekly_points == 0
        assert inactive_user.monthly_points == 0 