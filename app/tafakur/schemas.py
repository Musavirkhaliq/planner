from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime

class TagBase(BaseModel):
    tag_name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    reflection_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ReflectionBase(BaseModel):
    reflection_date: date
    mood: Optional[str] = None
    highlights: Optional[str] = None
    challenges: Optional[str] = None
    gratitude: Optional[str] = None
    lessons: Optional[str] = None
    tomorrow_goals: Optional[str] = None
    private: bool = True

class ReflectionCreate(ReflectionBase):
    tags: Optional[List[str]] = None

class ReflectionUpdate(BaseModel):
    mood: Optional[str] = None
    highlights: Optional[str] = None
    challenges: Optional[str] = None
    gratitude: Optional[str] = None
    lessons: Optional[str] = None
    tomorrow_goals: Optional[str] = None
    private: Optional[bool] = None
    tags: Optional[List[str]] = None

class Reflection(ReflectionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    tags: List[Tag] = []

    class Config:
        from_attributes = True

class ReflectionInsight(BaseModel):
    """Used for providing insights and analytics on reflections"""
    date_range: List[date]
    mood_distribution: dict
    common_tags: List[dict]
    streak: int  # Number of consecutive days with reflections
    total_reflections: int
    word_frequency: dict  # Word frequency analysis from reflection text
    improvement_areas: List[str]  # Areas frequently mentioned in challenges

class ReflectionStreak(BaseModel):
    """For tracking reflection consistency"""
    current_streak: int
    longest_streak: int
    last_reflection_date: date 