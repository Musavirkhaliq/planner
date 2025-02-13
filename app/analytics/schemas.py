from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

class TimeSlotAnalytics(BaseModel):
    total_slots: int
    completed_slots: int
    in_progress_slots: int
    not_started_slots: int
    total_minutes_reported: int
    average_minutes_per_slot: float
    completion_rate: float

class DailyAnalytics(BaseModel):
    date: date
    total_slots: int
    completed_slots: int
    total_minutes: int
    completion_rate: float

class TimeRangeAnalytics(BaseModel):
    start_date: date
    end_date: date
    daily_analytics: List[DailyAnalytics]
    total_slots: int
    total_completed: int
    total_minutes: int
    average_completion_rate: float