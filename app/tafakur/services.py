from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict
from collections import Counter
import re

from app.tafakur import schemas
from app.models import Reflection, ReflectionTag
from app.momentum.services import MomentumService
from app.momentum.momentum import REFLECTION_STREAK_MILESTONES 

class TafakurService:
    def __init__(self, db: Session):
        self.db = db

    # --- CRUD Operations ---
    
    def get_reflection(self, user_id: int, reflection_id: int) -> Optional[schemas.Reflection]:
        """Get a single reflection by ID for a user"""
        return self.db.query(Reflection).filter(
            Reflection.id == reflection_id,
            Reflection.user_id == user_id
        ).first()
    
    def get_reflection_by_date(self, user_id: int, reflection_date: date) -> Optional[schemas.Reflection]:
        """Get a reflection for a specific date"""
        return self.db.query(Reflection).filter(
            Reflection.user_id == user_id,
            Reflection.reflection_date == reflection_date
        ).first()
    
    def get_reflections(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[schemas.Reflection]:
        """Get all reflections for a user with optional date filtering"""
        query = self.db.query(Reflection).filter(Reflection.user_id == user_id)
        
        if from_date:
            query = query.filter(Reflection.reflection_date >= from_date)
        
        if to_date:
            query = query.filter(Reflection.reflection_date <= to_date)
        
        return query.order_by(desc(Reflection.reflection_date)).offset(skip).limit(limit).all()
    
    async def create_reflection(self, user_id: int, reflection: schemas.ReflectionCreate) -> schemas.Reflection:
        """Create a new reflection"""
        # Check if reflection already exists for this date
        existing = self.get_reflection_by_date(user_id, reflection.reflection_date)
        if existing:
            # Update instead of creating new
            return self.update_reflection(user_id, existing.id, schemas.ReflectionUpdate(**reflection.dict()))
        
        # Create new reflection
        db_reflection = Reflection(
            user_id=user_id,
            reflection_date=reflection.reflection_date,
            mood=reflection.mood,
            highlights=reflection.highlights,
            challenges=reflection.challenges,
            gratitude=reflection.gratitude,
            lessons=reflection.lessons,
            tomorrow_goals=reflection.tomorrow_goals,
            private=reflection.private
        )
        self.db.add(db_reflection)
        self.db.commit()
        self.db.refresh(db_reflection)
        
        # Process tags if provided
        if reflection.tags:
            for tag_name in reflection.tags:
                tag = ReflectionTag(
                    reflection_id=db_reflection.id,
                    tag_name=tag_name.lower().strip()
                )
                self.db.add(tag)
            
            self.db.commit()
            self.db.refresh(db_reflection)
        
        # Update reflection streak
        self._update_streak(user_id)
        
        # Award momentum points if applicable
        await self._award_reflection_points(user_id)
        
        return db_reflection
    
    def update_reflection(
        self, 
        user_id: int, 
        reflection_id: int, 
        reflection_update: schemas.ReflectionUpdate
    ) -> Optional[schemas.Reflection]:
        """Update an existing reflection"""
        db_reflection = self.get_reflection(user_id, reflection_id)
        if not db_reflection:
            return None
        
        # Update fields if provided
        update_data = reflection_update.dict(exclude_unset=True)
        tags_data = update_data.pop('tags', None)
        
        for key, value in update_data.items():
            setattr(db_reflection, key, value)
        
        # Update tags if provided
        if tags_data is not None:
            # Remove existing tags
            self.db.query(ReflectionTag).filter(
                ReflectionTag.reflection_id == reflection_id
            ).delete()
            
            # Add new tags
            for tag_name in tags_data:
                tag = ReflectionTag(
                    reflection_id=db_reflection.id,
                    tag_name=tag_name.lower().strip()
                )
                self.db.add(tag)
        
        self.db.commit()
        self.db.refresh(db_reflection)
        return db_reflection
    
    def delete_reflection(self, user_id: int, reflection_id: int) -> bool:
        """Delete a reflection"""
        db_reflection = self.get_reflection(user_id, reflection_id)
        if not db_reflection:
            return False
        
        self.db.delete(db_reflection)
        self.db.commit()
        
        # Update streak after deletion
        self._update_streak(user_id)
        
        return True
    
    # --- Analytics and Insights ---
    
    def get_reflection_streak(self, user_id: int) -> schemas.ReflectionStreak:
        """Get the current and longest streak of daily reflections"""
        # Get all reflection dates for the user
        reflection_dates = [
            r.reflection_date for r in self.db.query(Reflection.reflection_date)
            .filter(Reflection.user_id == user_id)
            .order_by(Reflection.reflection_date)
            .all()
        ]
        
        if not reflection_dates:
            return schemas.ReflectionStreak(
                current_streak=0,
                longest_streak=0,
                last_reflection_date=date.today()
            )
        
        # Calculate current streak
        current_streak = 0
        last_date = reflection_dates[-1]
        
        # If the last reflection isn't today or yesterday, streak is broken
        if last_date < date.today() - timedelta(days=1):
            current_streak = 0
        else:
            # Count backwards from the most recent date
            check_date = last_date
            while reflection_dates and check_date in reflection_dates:
                current_streak += 1
                check_date -= timedelta(days=1)
        
        # Calculate longest streak
        longest_streak = 0
        current_run = 1
        
        for i in range(1, len(reflection_dates)):
            if reflection_dates[i] == reflection_dates[i-1] + timedelta(days=1):
                current_run += 1
            else:
                current_run = 1
            
            longest_streak = max(longest_streak, current_run)
        
        # If we only have one reflection, longest streak is 1
        if len(reflection_dates) == 1:
            longest_streak = 1
        
        return schemas.ReflectionStreak(
            current_streak=current_streak,
            longest_streak=longest_streak,
            last_reflection_date=last_date
        )
    
    def get_insights(
        self, 
        user_id: int, 
        from_date: Optional[date] = None, 
        to_date: Optional[date] = None
    ) -> schemas.ReflectionInsight:
        """Generate insights from user's reflections"""
        # Default to last 30 days if no date range provided
        if not to_date:
            to_date = date.today()
        
        if not from_date:
            from_date = to_date - timedelta(days=30)
        
        # Get reflections in the date range
        reflections = self.get_reflections(
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            limit=1000  # High limit to get all in range
        )
        
        # Generate date range for the period
        date_range = []
        current_date = from_date
        while current_date <= to_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Calculate mood distribution
        mood_distribution = {}
        for r in reflections:
            if r.mood:
                mood_distribution[r.mood] = mood_distribution.get(r.mood, 0) + 1
        
        # Get common tags
        tags = []
        for r in reflections:
            for tag in r.tags:
                tags.append(tag.tag_name)
        
        tag_counts = Counter(tags)
        common_tags = [{"tag": tag, "count": count} for tag, count in tag_counts.most_common(10)]
        
        # Get streak information
        streak_info = self.get_reflection_streak(user_id)
        
        # Get word frequency analysis
        word_frequency = self._analyze_word_frequency(reflections)
        
        # Identify improvement areas from challenges
        improvement_areas = self._identify_improvement_areas(reflections)
        
        return schemas.ReflectionInsight(
            date_range=date_range,
            mood_distribution=mood_distribution,
            common_tags=common_tags,
            streak=streak_info.current_streak,
            total_reflections=len(reflections),
            word_frequency=word_frequency,
            improvement_areas=improvement_areas
        )
    
    # --- Helper Methods ---
    
    def _update_streak(self, user_id: int) -> None:
        """Update the user's reflection streak after changes"""
        # Implementation is internal to the service, so we reuse the public method
        self.get_reflection_streak(user_id)
    
    async def _award_reflection_points(self, user_id: int) -> None:
        """Award momentum points for completing reflections"""
        # Try to get MomentumService to award points
        try:
            
            momentum_service = MomentumService(self.db)
            # Award points for completing a reflection
            await momentum_service.process_event(user_id, "reflection_completion")
            
            # Check if this completes a streak achievement
            streak_info = self.get_reflection_streak(user_id)
            
            # If reflection streak hits certain thresholds, award bonus points
            for milestone in REFLECTION_STREAK_MILESTONES:
                if streak_info.current_streak == milestone:
                    await momentum_service.process_event(
                        user_id, 
                        "reflection_streak", 
                        {"streak": milestone}
                    )
        except ImportError:
            # Momentum module not available, skip awarding points
            pass
        except Exception as e:
            # Log error but don't fail the reflection creation
            print(f"Error awarding reflection points: {str(e)}")
            pass
    
    def _analyze_word_frequency(self, reflections: List[Reflection]) -> Dict[str, int]:
        """Analyze word frequency across all reflection fields"""
        # Common words to exclude
        stop_words = {
            "the", "and", "a", "to", "of", "in", "i", "is", "that", "it", 
            "for", "you", "was", "with", "on", "my", "have", "this", "be",
            "as", "at", "are", "but", "or", "from", "an", "they", "we", 
            "their", "there", "by", "so", "if", "will", "not", "can", "all",
            "what", "which", "when", "one", "would", "me", "has", "very",
            "them", "about", "who", "been", "had", "your", "more", "also", "do"
        }
        
        # Combine all text fields
        all_text = ""
        for r in reflections:
            fields = [r.highlights, r.challenges, r.gratitude, r.lessons, r.tomorrow_goals]
            all_text += " ".join([f for f in fields if f])
        
        # Split into words and count
        words = re.findall(r'\b\w+\b', all_text.lower())
        words = [w for w in words if w not in stop_words and len(w) > 2]
        
        word_counts = Counter(words)
        return dict(word_counts.most_common(20))
    
    def _identify_improvement_areas(self, reflections: List[Reflection]) -> List[str]:
        """Identify common themes in challenges field"""
        # Combine all challenges text
        challenges_text = ""
        for r in reflections:
            if r.challenges:
                challenges_text += r.challenges + " "
        
        # Simple approach: split into sentences and find most common phrases
        import re
        sentences = re.split(r'[.!?]', challenges_text)
        phrases = []
        
        for sentence in sentences:
            if len(sentence.strip()) > 10:  # Ignore very short sentences
                phrases.append(sentence.strip())
        
        # Very basic theme extraction - could be improved with NLP
        # Return at most 5 improvement areas
        return phrases[:5] if phrases else [] 