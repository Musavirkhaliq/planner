from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TimeSlotBase(BaseModel):
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    report_minutes: Optional[int] = None
    done: Optional[bool] = False

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlotUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    report_minutes: Optional[int] = None
    done: Optional[bool] = None

class TimeSlot(TimeSlotBase): 
    id: int
    owner_id: int

    class Config:
        from_attributes = True 