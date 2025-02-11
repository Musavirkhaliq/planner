from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

class Analytics(BaseModel):
    total_tasks: int
    completed_tasks: int
    total_time_spent: int
    timeslot_analytics: List[dict]  # New field for timeslot analytics

class TimeSlotBase(BaseModel):
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    report_minutes: Optional[int] = None
    done: Optional[str] = "Not Started"

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlotUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    report_minutes: Optional[int] = None
    done: Optional[str] = "Not Started"

class TimeSlot(TimeSlotBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True