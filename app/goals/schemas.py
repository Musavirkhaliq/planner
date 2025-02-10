from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class GoalStepBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class GoalStepCreate(GoalStepBase):
    pass

class GoalStep(GoalStepBase):
    id: int
    goal_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class GoalBase(BaseModel):
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None

class GoalCreate(GoalBase):
    pass

class Goal(GoalBase):
    id: int
    owner_id: int
    created_at: datetime
    steps: List[GoalStep] = []

    class Config:
        from_attributes = True 