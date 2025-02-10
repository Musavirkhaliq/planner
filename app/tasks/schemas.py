from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    completed: Optional[bool] = None
    time_spent: Optional[int] = None

class Task(TaskBase):
    id: int
    owner_id: int
    completed: bool = False
    time_spent: int = 0
    created_at: datetime

    class Config:
        from_attributes = True 