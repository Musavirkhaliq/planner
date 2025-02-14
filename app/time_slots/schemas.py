from pydantic import BaseModel,Field
from typing import Optional
from datetime import datetime

class TimeSlotBase(BaseModel):
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    report_minutes: Optional[int] = None
    status: Optional[str] = Field(default="not_started", description="Status of the time slot: completed, in_progress, not_started")

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlotUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    report_minutes: Optional[int] = None
    status: Optional[str] = Field(None, description="Status of the time slot: completed, in_progress, not_started")

    class Config:
        orm_mode = True
class TimeSlot(TimeSlotBase): 
    id: int
    owner_id: int

    class Config:
        from_attributes = True 