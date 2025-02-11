from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict
from datetime import date, datetime, timedelta
from ..models import Task, TimeSlot
from .schemas import TimeSlotCreate, TimeSlotUpdate, Analytics

def get_user_analytics(db: Session, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None):
    tasks = db.query(Task).filter(Task.owner_id == user_id).all()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.completed)
    total_time = sum(t.time_spent for t in tasks)

    # Timeslot analytics
    timeslots = db.query(TimeSlot).filter(TimeSlot.owner_id == user_id)
    if start_date and end_date:
        timeslots = timeslots.filter(TimeSlot.start_time >= start_date, TimeSlot.end_time <= end_date)

    timeslot_analytics = []
    total_slots = 0
    utilized_slots = 0
    total_focus_time = 0
    focus_time_distribution = []
    productivity_trends = []

    for slot in timeslots:
        total_slots += 1
        if slot.done:
            utilized_slots += 1
        focus_time = slot.report_minutes or 0
        total_focus_time += focus_time
        focus_time_distribution.append({
            "start_time": slot.start_time,
            "focus_time": focus_time
        })
        timeslot_analytics.append({
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "minutes_focused": focus_time,
            "description": slot.description,
            "done": slot.done
        })

    # Calculate productivity trends (daily)
    if start_date and end_date:
        current_date = start_date
        while current_date <= end_date:
            daily_slots = db.query(TimeSlot).filter(
                TimeSlot.owner_id == user_id,
                func.date(TimeSlot.start_time) == current_date
            ).all()
            daily_focus_time = sum(slot.report_minutes or 0 for slot in daily_slots)
            productivity_trends.append({
                "date": current_date,
                "focus_time": daily_focus_time
            })
            current_date += timedelta(days=1)

    # Calculate metrics
    time_slot_utilization = (utilized_slots / total_slots * 100) if total_slots > 0 else 0
    task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    average_focus_per_slot = (total_focus_time / total_slots) if total_slots > 0 else 0

    return Analytics(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        total_time_spent=total_time,
        timeslot_analytics=timeslot_analytics,
        time_slot_utilization=time_slot_utilization,
        task_completion_rate=task_completion_rate,
        focus_time_distribution=focus_time_distribution,
        productivity_trends=productivity_trends,
        average_focus_per_slot=average_focus_per_slot
    )

def get_time_slots(db: Session, user_id: int, date: Optional[date] = None):
    query = db.query(TimeSlot).filter(TimeSlot.owner_id == user_id)
    
    if date:
        query = query.filter(func.date(TimeSlot.start_time) == date)
    
    return query.order_by(TimeSlot.start_time).all()

def get_time_slot(db: Session, slot_id: int, user_id: int):
    return db.query(TimeSlot).filter(
        TimeSlot.id == slot_id,
        TimeSlot.owner_id == user_id
    ).first()

def create_time_slot(db: Session, time_slot: TimeSlotCreate, owner_id: int):
    db_time_slot = TimeSlot(**time_slot.dict(), owner_id=owner_id)
    db.add(db_time_slot)
    db.commit()
    db.refresh(db_time_slot)
    return db_time_slot

def update_time_slot(db: Session, slot: TimeSlot, update: TimeSlotUpdate):
    for key, value in update.dict(exclude_unset=True).items():
        set