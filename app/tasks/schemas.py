from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(default="medium", description="Priority level: low, medium, high")
    status: Optional[str] = Field(default="not_started", description="Status: not_started, in_progress, completed")
    complexity: Optional[str] = Field(default="medium", description="Complexity level: low, medium, high")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    complexity: Optional[str] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Task(TaskBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True 