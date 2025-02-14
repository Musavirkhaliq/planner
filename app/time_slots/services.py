from sqlalchemy.orm import Session
from . import schemas
from .. import models
from typing import Optional
from datetime import date,timedelta

def get_time_slots(db: Session, user_id: int, date: Optional[date] = None):
    query = db.query(models.TimeSlot).filter(models.TimeSlot.owner_id == user_id)
    if date:
        query = query.filter(models.TimeSlot.start_time >= date, models.TimeSlot.end_time < date + timedelta(days=1))
    return query.all()

def get_time_slot(db: Session, slot_id: int, user_id: int):
    return db.query(models.TimeSlot).filter(models.TimeSlot.id == slot_id, models.TimeSlot.owner_id == user_id).first()

def create_time_slot(db: Session, time_slot: schemas.TimeSlotCreate, owner_id: int):
    db_time_slot = models.TimeSlot(**time_slot.model_dump(), owner_id=owner_id)  # Updated for Pydantic v2
    db.add(db_time_slot)
    db.commit()
    db.refresh(db_time_slot)
    return db_time_slot

def update_time_slot(db: Session, time_slot: models.TimeSlot, update: schemas.TimeSlotUpdate):
    for key, value in update.model_dump(exclude_unset=True).items():  # Updated for Pydantic v2
        setattr(time_slot, key, value)
    db.commit()
    db.refresh(time_slot)
    return time_slot