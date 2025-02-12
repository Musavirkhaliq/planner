from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class ProductivityAnalytics(BaseModel):
    total_time_slots: int
    completed_time_slots: int
    time_slot_completion_rate: float  # completed time slots / total time slots
    total_tasks: int
    completed_tasks: int
    task_completion_rate: float       # completed tasks / total tasks
    total_time_spent: float           # in hours
    average_time_slot_duration: float # in hours
    average_task_completion_time: float  # in hours, for tasks linked to time slots
    average_tasks_per_day: float
    most_productive_day: Optional[date]
    least_productive_day: Optional[date]

class GoalProgressAnalytics(BaseModel):
    total_goals: int
    completed_goals: int
    in_progress_goals: int
    not_started_goals: int
    completion_percentage: float      # as a percentage

class TimeSlotDistribution(BaseModel):
    date: date
    total_time_slots: int
    completed_time_slots: int

class AnalyticsResponse(BaseModel):
    productivity: ProductivityAnalytics
    goal_progress: GoalProgressAnalytics
    time_slot_distribution: List[TimeSlotDistribution]

class DailyProductivityAnalytics(BaseModel):
    date: date
    total_time_slots: int
    completed_time_slots: int
    total_tasks: int
    completed_tasks: int
    total_time_spent: float  # in hours
