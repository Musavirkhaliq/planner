# app/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class TokenData(BaseModel):
    email: str | None = None

class TaskBase(BaseModel):
    title: str
    description: str

class TaskCreate(TaskBase):
    pass

# New: for updating a task (e.g. marking complete, updating time spent)
class TaskUpdate(BaseModel):
    completed: bool | None = None
    time_spent: float | None = None

class Task(TaskBase):
    id: int
    completed: bool
    time_spent: float
    owner_id: int

    class Config:
        orm_mode = True

class GoalBase(BaseModel):
    title: str
    description: str

class GoalCreate(GoalBase):
    pass

class Goal(GoalBase):
    id: int
    completed: bool
    owner_id: int

    class Config:
        orm_mode = True

class GoalStepBase(BaseModel):
    title: str

class GoalStepCreate(GoalStepBase):
    pass

class GoalStep(GoalStepBase):
    id: int
    completed: bool
    goal_id: int

    class Config:
        orm_mode = True

class TimeSlotBase(BaseModel):
    start_time: datetime
    end_time: datetime
    description: str

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlot(TimeSlotBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

# New: Dashboard settings schema stub
class DashboardSettings(BaseModel):
    theme: str = "light"
    layout: str = "daily"  # could be "daily", "weekly", or "monthly"

class TimeSlotUpdate(BaseModel):
    report_minutes: Optional[int] = None
    done: Optional[bool] = None