from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class GoalBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(default="medium", description="Priority level: low, medium, high")
    status: Optional[str] = Field(default="not_started", description="Status: not_started, in_progress, completed")

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GoalStepBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = Field(default="not_started", description="Status: not_started, in_progress, completed")

class GoalStepCreate(GoalStepBase):
    goal_id: int

class GoalStepUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GoalStep(GoalStepBase):
    id: int
    goal_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Goal(GoalBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[GoalStep] = []

    class Config:
        from_attributes = True 