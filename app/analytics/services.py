from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
from typing import List, Dict
from ..models import TimeSlot, Task, Goal
from .schemas import (
    ProductivityAnalytics,
    GoalProgressAnalytics,
    TimeSlotDistribution,
    DailyProductivityAnalytics
)

def calculate_productivity_analytics(db: Session, user_id: int, start_date: date, end_date: date) -> ProductivityAnalytics:
    # Query time slots in the given date range.
    # Note: Using datetime.combine to cover the whole day.
    time_slots = db.query(TimeSlot).filter(
        TimeSlot.owner_id == user_id,
        TimeSlot.start_time >= datetime.combine(start_date, datetime.min.time()),
        TimeSlot.end_time <= datetime.combine(end_date, datetime.max.time())
    ).all()
    total_time_slots = len(time_slots)
    completed_time_slots = len([ts for ts in time_slots if ts.status == "completed"])
    time_slot_completion_rate = (completed_time_slots / total_time_slots) if total_time_slots > 0 else 0.0

    # Query tasks created in the same date range.
    tasks = db.query(Task).filter(
        Task.owner_id == user_id,
        Task.created_at >= datetime.combine(start_date, datetime.min.time()),
        Task.created_at <= datetime.combine(end_date, datetime.max.time())
    ).all()
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == "completed"])
    task_completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0.0

    # Total time spent (in hours) on time slots.
    total_time_spent = sum((ts.end_time - ts.start_time).total_seconds() / 3600 for ts in time_slots)
    average_time_slot_duration = (total_time_spent / total_time_slots) if total_time_slots > 0 else 0.0

    # Average task completion time based on time slots that are completed and have an associated task.
    completed_time_slots_with_tasks = [ts for ts in time_slots if ts.status == "completed" and getattr(ts, 'task', None)]
    if completed_time_slots_with_tasks:
        average_task_completion_time = sum(
            (ts.end_time - ts.start_time).total_seconds() / 3600 for ts in completed_time_slots_with_tasks
        ) / len(completed_time_slots_with_tasks)
    else:
        average_task_completion_time = 0.0

    # Calculate the average number of tasks created per day.
    num_days = (end_date - start_date).days + 1
    average_tasks_per_day = (total_tasks / num_days) if num_days > 0 else 0.0

    # Compute daily total time spent to find the most and least productive days.
    daily_productivity: Dict[date, float] = {}
    for ts in time_slots:
        day = ts.start_time.date()
        daily_productivity[day] = daily_productivity.get(day, 0.0) + (ts.end_time - ts.start_time).total_seconds() / 3600

    most_productive_day = max(daily_productivity, key=daily_productivity.get) if daily_productivity else None
    least_productive_day = min(daily_productivity, key=daily_productivity.get) if daily_productivity else None

    return ProductivityAnalytics(
        total_time_slots=total_time_slots,
        completed_time_slots=completed_time_slots,
        time_slot_completion_rate=round(time_slot_completion_rate, 2),
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        task_completion_rate=round(task_completion_rate, 2),
        total_time_spent=round(total_time_spent, 2),
        average_time_slot_duration=round(average_time_slot_duration, 2),
        average_task_completion_time=round(average_task_completion_time, 2),
        average_tasks_per_day=round(average_tasks_per_day, 2),
        most_productive_day=most_productive_day,
        least_productive_day=least_productive_day
    )

def calculate_goal_progress_analytics(db: Session, user_id: int) -> GoalProgressAnalytics:
    goals = db.query(Goal).filter(Goal.owner_id == user_id).all()
    total_goals = len(goals)
    completed_goals = len([g for g in goals if g.status == "completed"])
    in_progress_goals = len([g for g in goals if g.status == "in_progress"])
    not_started_goals = len([g for g in goals if g.status == "not_started"])
    completion_percentage = (completed_goals / total_goals) if total_goals > 0 else 0.0

    return GoalProgressAnalytics(
        total_goals=total_goals,
        completed_goals=completed_goals,
        in_progress_goals=in_progress_goals,
        not_started_goals=not_started_goals,
        completion_percentage=round(completion_percentage * 100, 2)  # expressed as a percentage
    )

def calculate_time_slot_distribution(db: Session, user_id: int, start_date: date, end_date: date) -> List[TimeSlotDistribution]:
    time_slots = db.query(TimeSlot).filter(
        TimeSlot.owner_id == user_id,
        TimeSlot.start_time >= datetime.combine(start_date, datetime.min.time()),
        TimeSlot.end_time <= datetime.combine(end_date, datetime.max.time())
    ).all()

    # Build a dictionary with a summary for each day.
    distribution: Dict[date, Dict[str, int]] = {}
    for ts in time_slots:
        day = ts.start_time.date()
        if day not in distribution:
            distribution[day] = {"total": 0, "completed": 0}
        distribution[day]["total"] += 1
        if ts.status == "completed":
            distribution[day]["completed"] += 1

    # Ensure every day in the range is represented (even if there are zero records).
    result = []
    current_day = start_date
    while current_day <= end_date:
        day_data = distribution.get(current_day, {"total": 0, "completed": 0})
        result.append(TimeSlotDistribution(
            date=current_day,
            total_time_slots=day_data["total"],
            completed_time_slots=day_data["completed"]
        ))
        current_day += timedelta(days=1)
    return result

def calculate_daily_productivity(db: Session, user_id: int, start_date: date, end_date: date) -> List[DailyProductivityAnalytics]:
    """
    Returns a daily breakdown of productivity including counts of time slots and tasks,
    as well as total time spent per day.
    """
    time_slots = db.query(TimeSlot).filter(
        TimeSlot.owner_id == user_id,
        TimeSlot.start_time >= datetime.combine(start_date, datetime.min.time()),
        TimeSlot.end_time <= datetime.combine(end_date, datetime.max.time())
    ).all()

    tasks = db.query(Task).filter(
        Task.owner_id == user_id,
        Task.created_at >= datetime.combine(start_date, datetime.min.time()),
        Task.created_at <= datetime.combine(end_date, datetime.max.time())
    ).all()

    # Initialize a dictionary for every day in the range.
    daily_data: Dict[date, DailyProductivityAnalytics] = {}
    current_day = start_date
    while current_day <= end_date:
        daily_data[current_day] = DailyProductivityAnalytics(
            date=current_day,
            total_time_slots=0,
            completed_time_slots=0,
            total_tasks=0,
            completed_tasks=0,
            total_time_spent=0.0
        )
        current_day += timedelta(days=1)

    # Tally time slots and time spent per day.
    for ts in time_slots:
        day = ts.start_time.date()
        if day in daily_data:
            daily_data[day].total_time_slots += 1
            if ts.status == "completed":
                daily_data[day].completed_time_slots += 1
            daily_data[day].total_time_spent += (ts.end_time - ts.start_time).total_seconds() / 3600

    # Tally tasks per day.
    for task in tasks:
        day = task.created_at.date()
        if day in daily_data:
            daily_data[day].total_tasks += 1
            if task.status == "completed":
                daily_data[day].completed_tasks += 1

    # Return the results as a sorted list (by date).
    return [daily_data[day] for day in sorted(daily_data.keys())]
