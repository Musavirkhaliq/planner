import pytest
from datetime import date, datetime, timedelta
import random

from app.tafakur.services import TafakurService
from app.tafakur.models import Reflection, ReflectionTag
from app.tafakur.schemas import ReflectionCreate, ReflectionUpdate, ReflectionStreak

@pytest.mark.tafakur
@pytest.mark.service
class TestTafakurService:
    """Tests for the TafakurService functionality"""
    
    @pytest.fixture
    def tafakur_service(self, db_session):
        """Create a TafakurService instance"""
        return TafakurService(db_session)
    
    def test_get_reflection_by_date(self, tafakur_service, user_with_reflection):
        """Test retrieving a reflection by date"""
        user, reflection = user_with_reflection
        
        # Get the reflection using the service
        result = tafakur_service.get_reflection_by_date(user.id, date.today())
        
        # Verify we got the correct reflection
        assert result is not None
        assert result.id == reflection.id
        assert result.reflection_date == date.today()
        assert result.user_id == user.id
    
    def test_get_reflection_by_id(self, tafakur_service, user_with_reflection):
        """Test retrieving a reflection by ID"""
        user, reflection = user_with_reflection
        
        # Get the reflection using the service
        result = tafakur_service.get_reflection(user.id, reflection.id)
        
        # Verify we got the correct reflection
        assert result is not None
        assert result.id == reflection.id
        assert result.mood == reflection.mood
        assert result.highlights == reflection.highlights
    
    @pytest.mark.model
    def test_get_reflections_with_date_filtering(self, db_session, tafakur_service, test_user_with_momentum):
        """Test retrieving reflections with date filtering"""
        # Create reflections for different dates
        today = date.today()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        
        # Create reflections
        reflections = [
            Reflection(
                user_id=test_user_with_momentum.id,
                reflection_date=today,
                mood="Good",
                highlights="Today's reflection"
            ),
            Reflection(
                user_id=test_user_with_momentum.id,
                reflection_date=yesterday,
                mood="Okay",
                highlights="Yesterday's reflection"
            ),
            Reflection(
                user_id=test_user_with_momentum.id,
                reflection_date=last_week,
                mood="Great",
                highlights="Last week's reflection"
            )
        ]
        
        for reflection in reflections:
            db_session.add(reflection)
        db_session.commit()
        
        # Test filtering by from_date
        result = tafakur_service.get_reflections(
            user_id=test_user_with_momentum.id,
            from_date=yesterday
        )
        assert len(result) == 2  # Today and yesterday
        
        # Test filtering by to_date
        result = tafakur_service.get_reflections(
            user_id=test_user_with_momentum.id,
            to_date=yesterday
        )
        assert len(result) == 2  # Yesterday and last week
        
        # Test filtering by from_date and to_date
        result = tafakur_service.get_reflections(
            user_id=test_user_with_momentum.id,
            from_date=yesterday,
            to_date=yesterday
        )
        assert len(result) == 1  # Only yesterday
    
    @pytest.mark.asyncio
    async def test_create_reflection(self, db_session, tafakur_service, test_user_with_momentum):
        """Test creating a reflection"""
        # Create reflection data
        reflection_data = ReflectionCreate(
            reflection_date=date.today(),
            mood="Great",
            highlights="Accomplished a lot",
            challenges="Some distractions",
            gratitude="Family and friends",
            lessons="Stay focused",
            tomorrow_goals="Complete project",
            tags=["productivity", "focus"]
        )
        
        # Create the reflection
        result = await tafakur_service.create_reflection(test_user_with_momentum.id, reflection_data)
        
        # Verify the reflection was created correctly
        assert result is not None
        assert result.reflection_date == date.today()
        assert result.mood == "Great"
        assert result.highlights == "Accomplished a lot"
        assert result.user_id == test_user_with_momentum.id
        
        # Verify tags were created
        assert len(result.tags) == 2
        tag_names = [tag.tag_name for tag in result.tags]
        assert "productivity" in tag_names
        assert "focus" in tag_names
    
    def test_update_reflection(self, db_session, tafakur_service, user_with_reflection):
        """Test updating a reflection"""
        user, reflection = user_with_reflection
        
        # Create update data
        update_data = ReflectionUpdate(
            mood="Great",  # Changed from "Good"
            highlights="Updated highlights",
            tags=["productivity", "focus", "health"]  # Added "health"
        )
        
        # Update the reflection
        result = tafakur_service.update_reflection(user.id, reflection.id, update_data)
        
        # Verify the reflection was updated correctly
        assert result is not None
        assert result.mood == "Great"
        assert result.highlights == "Updated highlights"
        
        # Unchanged fields should remain the same
        assert result.challenges == reflection.challenges
        assert result.gratitude == reflection.gratitude
        
        # Verify tags were updated
        assert len(result.tags) == 3
        tag_names = [tag.tag_name for tag in result.tags]
        assert "health" in tag_names
    
    def test_delete_reflection(self, db_session, tafakur_service, user_with_reflection):
        """Test deleting a reflection"""
        user, reflection = user_with_reflection
        
        # Delete the reflection
        result = tafakur_service.delete_reflection(user.id, reflection.id)
        
        # Verify deletion was successful
        assert result is True
        
        # Verify the reflection no longer exists
        deleted_reflection = db_session.query(Reflection).filter(
            Reflection.id == reflection.id
        ).first()
        assert deleted_reflection is None
        
        # Verify tags were also deleted
        tags = db_session.query(ReflectionTag).filter(
            ReflectionTag.reflection_id == reflection.id
        ).all()
        assert len(tags) == 0
    
    @pytest.mark.model
    def test_get_reflection_streak(self, db_session, tafakur_service, test_user_with_momentum):
        """Test getting reflection streak information"""
        # Create reflections for consecutive days
        today = date.today()
        yesterday = today - timedelta(days=1)
        day_before_yesterday = today - timedelta(days=2)
        
        # Create reflections for consecutive days
        reflections = [
            Reflection(
                user_id=test_user_with_momentum.id,
                reflection_date=today,
                mood="Good"
            ),
            Reflection(
                user_id=test_user_with_momentum.id,
                reflection_date=yesterday,
                mood="Okay"
            ),
            Reflection(
                user_id=test_user_with_momentum.id,
                reflection_date=day_before_yesterday,
                mood="Great"
            )
        ]
        
        for reflection in reflections:
            db_session.add(reflection)
        db_session.commit()
        
        # Get streak
        streak = tafakur_service.get_reflection_streak(test_user_with_momentum.id)
        
        # Verify streak information
        assert streak.current_streak == 3
        assert streak.longest_streak == 3
        assert streak.last_reflection_date == today
    
    @pytest.mark.model
    def test_streak_broken(self, db_session, tafakur_service, test_user_with_momentum):
        """Test streak calculation when streak is broken"""
        # Create reflections with a gap
        today = date.today()
        three_days_ago = today - timedelta(days=3)
        four_days_ago = today - timedelta(days=4)
        
        # Create reflections with a gap
        reflections = [
            Reflection(
                user_id=test_user_with_momentum.id,
                reflection_date=today,
                mood="Good"
            ),
            Reflection(
                user_id=test_user_with_momentum.id,
                reflection_date=three_days_ago,
                mood="Okay"
            ),
            Reflection(
                user_id=test_user_with_momentum.id,
                reflection_date=four_days_ago,
                mood="Great"
            )
        ]
        
        for reflection in reflections:
            db_session.add(reflection)
        db_session.commit()
        
        # Get streak
        streak = tafakur_service.get_reflection_streak(test_user_with_momentum.id)
        
        # Verify streak information
        assert streak.current_streak == 1  # Only today counts
        assert streak.longest_streak == 2  # Three and four days ago were consecutive
        assert streak.last_reflection_date == today
    
    def test_get_insights(self, db_session, tafakur_service, test_user_with_momentum):
        """Test getting insights from reflections"""
        # Create several reflections with different moods and tags
        today = date.today()
        reflections = []
        
        for i in range(10):
            day = today - timedelta(days=i)
            if i < 5:  # More recent days are "Good"
                mood = "Good"
            else:  # Older days are "Okay"
                mood = "Okay"
                
            reflection = Reflection(
                user_id=test_user_with_momentum.id,
                reflection_date=day,
                mood=mood,
                highlights=f"Day {i} highlights",
                challenges=f"Day {i} challenges",
                gratitude=f"Grateful for day {i}",
                private=True
            )
            reflections.append(reflection)
            db_session.add(reflection)
        
        db_session.commit()
        
        # Add tags to some reflections
        tags = [
            ("productivity", reflections[0].id),
            ("focus", reflections[0].id),
            ("productivity", reflections[1].id),
            ("health", reflections[2].id),
            ("focus", reflections[3].id),
            ("family", reflections[4].id)
        ]
        
        for tag_name, reflection_id in tags:
            tag = ReflectionTag(
                reflection_id=reflection_id,
                tag_name=tag_name
            )
            db_session.add(tag)
        
        db_session.commit()
        
        # Get insights for the last 7 days
        from_date = today - timedelta(days=6)
        insights = tafakur_service.get_insights(
            test_user_with_momentum.id,
            from_date=from_date
        )
        
        # Verify insights data
        assert len(insights.date_range) == 7  # 7 days
        assert len(insights.mood_distribution) == 2  # "Good" and "Okay"
        assert insights.total_reflections == 7  # 7 reflections in date range
        assert len(insights.common_tags) >= 3  # At least "productivity", "focus", "health"
        
        # Verify mood distribution
        assert "Good" in insights.mood_distribution
        assert insights.mood_distribution["Good"] >= 3  # At least days 0-2
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_award_reflection_points(self, db_session, tafakur_service, test_user_with_momentum):
        """Test that points are awarded for reflections"""
        # Get initial points
        initial_points = test_user_with_momentum.total_points
        
        # Create reflection data
        reflection_data = ReflectionCreate(
            reflection_date=date.today(),
            mood="Great",
            highlights="Test reflection"
        )
        
        # Create the reflection
        await tafakur_service.create_reflection(test_user_with_momentum.id, reflection_data)
        
        # Get updated user
        db_session.refresh(test_user_with_momentum)
        
        # Verify points were awarded
        assert test_user_with_momentum.total_points > initial_points 