# app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from .utils import get_password_hash
from datetime import date

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_tasks(db: Session, user_id: int):
    return db.query(models.Task).filter(models.Task.owner_id == user_id).all()

def get_task(db: Session, task_id: int, user_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == user_id).first()

def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    db_task = models.Task(**task.dict(), owner_id=user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task: models.Task, task_update: schemas.TaskUpdate):
    if task_update.completed is not None:
        task.completed = task_update.completed
    if task_update.time_spent is not None:
        task.time_spent = task_update.time_spent
    db.commit()
    db.refresh(task)
    return task

def get_goals(db: Session, user_id: int):
    return db.query(models.Goal).filter(models.Goal.owner_id == user_id).all()

def create_goal(db: Session, goal: schemas.GoalCreate, user_id: int):
    db_goal = models.Goal(**goal.dict(), owner_id=user_id)
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def create_goal_step(db: Session, step: schemas.GoalStepCreate, goal_id: int):
    db_step = models.GoalStep(**step.dict(), goal_id=goal_id)
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step

def get_time_slots(db: Session, user_id: int):
    return db.query(models.TimeSlot).filter(models.TimeSlot.owner_id == user_id).all()

def create_time_slot(db: Session, time_slot: schemas.TimeSlotCreate, owner_id: int):
    db_time_slot = models.TimeSlot(
        date=time_slot.date,  # Ensure this field is passed
        start_time=time_slot.start_time,
        end_time=time_slot.end_time,
        description=time_slot.description,
        owner_id=owner_id,
        report_minutes=time_slot.report_minutes,
        done=time_slot.done
    )
    db.add(db_time_slot)
    db.commit()
    db.refresh(db_time_slot)
    return db_time_slot


def get_time_slot(db: Session, slot_id: int, user_id: int):
    return db.query(models.TimeSlot).filter(
        models.TimeSlot.id == slot_id,
        models.TimeSlot.owner_id == user_id
    ).first()

def update_time_slot(db: Session, slot: models.TimeSlot, update: schemas.TimeSlotUpdate):
    if update.report_minutes is not None:
        slot.report_minutes = update.report_minutes
    if update.done is not None:
        slot.done = update.done
    db.commit()
    db.refresh(slot)
    return slot
def get_time_slots_by_date(db: Session, user_id: int, date: date):
    return db.query(models.TimeSlot).filter(
        models.TimeSlot.owner_id == user_id,
        models.TimeSlot.date == date
    ).all()