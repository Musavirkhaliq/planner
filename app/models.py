from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Float, event
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from sqlalchemy import Date
from .json_utils import serialize_json, deserialize_json

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    tasks = relationship("Task", back_populates="owner")
    goals = relationship("Goal", back_populates="owner")
    time_slots = relationship("TimeSlot", back_populates="owner")
    current_level_id = Column(Integer, ForeignKey("levels.id"), nullable=True)
    current_level = relationship("Level", back_populates="users", lazy="joined")
    achievements = relationship("UserAchievement", back_populates="user")
    streaks = relationship("Streak", back_populates="user")
    total_points = Column(Integer, default=0)
    weekly_points = Column(Integer, default=0)
    monthly_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    completed = Column(Boolean, default=False)
    time_spent = Column(Float, default=0.0)  # Time spent in hours
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="tasks")
    created_at = Column(DateTime, default=datetime.utcnow)

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    completed = Column(Boolean, default=False)
    steps = relationship("GoalStep", back_populates="goal")
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="goals")
    created_at = Column(DateTime, default=datetime.utcnow)

class GoalStep(Base):
    __tablename__ = "goal_steps"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    completed = Column(Boolean, default=False)
    goal_id = Column(Integer, ForeignKey("goals.id"))
    goal = relationship("Goal", back_populates="steps")
    created_at = Column(DateTime, default=datetime.utcnow)

class TimeSlot(Base):
    __tablename__ = "time_slots"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)  # New column to store the date
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="time_slots")

    report_minutes = Column(Integer, default=0)
    status = Column(String, default="not_started", nullable=False)  # New field
    created_at = Column(DateTime, default=datetime.utcnow)

class EmailVerification(Base):
    __tablename__ = "email_verifications"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    otp = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    points = Column(Integer, default=0)
    category = Column(String)  # e.g., 'productivity', 'consistency', 'milestone'
    criteria_type = Column(String)  # e.g., 'count', 'streak', 'time'
    criteria_value = Column(Integer)  # value needed to unlock
    icon_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    progress = Column(Integer, default=0)  # Current progress towards achievement
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")

class Streak(Base):
    __tablename__ = "streaks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    streak_type = Column(String)  # e.g., 'daily_tasks', 'weekly_goals'
    current_count = Column(Integer, default=0)
    longest_count = Column(Integer, default=0)
    last_activity_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="streaks")

class Level(Base):
    __tablename__ = "levels"
    id = Column(Integer, primary_key=True, index=True)
    level_number = Column(Integer, unique=True, nullable=False)
    points_required = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    perks = Column(String, nullable=False, default='{"can_create_goals":true,"can_track_time":true,"can_earn_achievements":true,"can_view_analytics":true}')
    users = relationship("User", back_populates="current_level", lazy="noload")

    def __init__(self, *args, **kwargs):
        if 'perks' in kwargs:
            kwargs['perks'] = serialize_json(kwargs['perks'])
        super().__init__(*args, **kwargs)

    @property
    def perks_dict(self):
        """Get perks as a dictionary."""
        return deserialize_json(self.perks)

    @perks_dict.setter
    def perks_dict(self, value):
        """Set perks from a dictionary."""
        self.perks = serialize_json(value)

# Add event listeners to handle JSON serialization
@event.listens_for(Level, 'before_update')
def receive_before_update(mapper, connection, target):
    if isinstance(target.perks, dict):
        target.perks = serialize_json(target.perks)

@event.listens_for(Level, 'load')
def receive_load(target, context):
    if target.perks:
        target._perks_dict = deserialize_json(target.perks)