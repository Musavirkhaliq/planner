from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date
from ..models import TimeSlot
from .schemas import TimeSlotCreate, TimeSlotUpdate

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
        setattr(slot, key, value)
    db.commit()
    db.refresh(slot)
    return slot 