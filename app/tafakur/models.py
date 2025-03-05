from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date, datetime

from app.database import Base

class Reflection(Base):
    """Daily reflection/contemplation model"""
    __tablename__ = "reflections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reflection_date = Column(Date, default=date.today, index=True)
    mood = Column(String(50), nullable=True)
    highlights = Column(Text, nullable=True)  # What went well
    challenges = Column(Text, nullable=True)  # What could be improved
    gratitude = Column(Text, nullable=True)  # What you're grateful for
    lessons = Column(Text, nullable=True)  # What you learned
    tomorrow_goals = Column(Text, nullable=True)  # Goals for tomorrow
    private = Column(Boolean, default=True)  # Whether this reflection is private
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="reflections")
    tags = relationship("ReflectionTag", back_populates="reflection", cascade="all, delete-orphan")

class ReflectionTag(Base):
    """Tags for reflections to enable categorization and searching"""
    __tablename__ = "reflection_tags"

    id = Column(Integer, primary_key=True, index=True)
    reflection_id = Column(Integer, ForeignKey("reflections.id"), nullable=False)
    tag_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    reflection = relationship("Reflection", back_populates="tags")

# Add this to the User model in app/models.py:
# reflections = relationship("Reflection", back_populates="user", cascade="all, delete-orphan") 