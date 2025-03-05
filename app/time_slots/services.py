from sqlalchemy.orm import Session
from . import schemas
from .. import models
from typing import Optional
from datetime import date, timedelta, datetime
from ..momentum.services import MomentumService

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

async def update_time_slot(db: Session, time_slot: models.TimeSlot, update: schemas.TimeSlotUpdate):
    old_status = time_slot.status
    
    # Update the time slot
    for key, value in update.model_dump(exclude_unset=True).items():  # Updated for Pydantic v2
        setattr(time_slot, key, value)
    
    momentum_service = MomentumService(db)
    
    # Check if status changed from completed to something else (task was uncompleted)
    if old_status == "completed" and update.status and update.status != "completed":
        # Calculate duration in minutes
        duration = int((time_slot.end_time - time_slot.start_time).total_seconds() / 60)
        
        # Revert time slot completion event
        await momentum_service.revert_event(
            user_id=time_slot.owner_id,
            event_type='time_slot_completion',
            metadata={
                'duration': duration,
                'completion_time': datetime.utcnow(),
                'is_weekend': datetime.utcnow().weekday() >= 5
            }
        )
        
        # If it was a focused session, revert that too
        if duration >= 25:  # Assuming focused sessions are 25+ minutes
            await momentum_service.revert_event(
                user_id=time_slot.owner_id,
                event_type='focused_session',
                metadata={
                    'duration': duration,
                    'completion_time': datetime.utcnow()
                }
            )
    
    # Check if status changed to completed
    elif update.status == "completed" and old_status != "completed":
        # Calculate duration in minutes
        duration = int((time_slot.end_time - time_slot.start_time).total_seconds() / 60)
        
        # Process time slot completion event
        await momentum_service.process_event(
            user_id=time_slot.owner_id,
            event_type='time_slot_completion',
            metadata={
                'duration': duration,
                'completion_time': datetime.utcnow(),
                'is_weekend': datetime.utcnow().weekday() >= 5
            }
        )
        
        # If it was a focused session (you might want to add a field to identify this)
        if duration >= 25:  # Assuming focused sessions are 25+ minutes
            await momentum_service.process_event(
                user_id=time_slot.owner_id,
                event_type='focused_session',
                metadata={
                    'duration': duration,
                    'completion_time': datetime.utcnow()
                }
            )
        
        # Check for early bird or night owl bonus
        hour = datetime.utcnow().hour
        if 5 <= hour < 9:
            await momentum_service.process_event(
                user_id=time_slot.owner_id,
                event_type='early_bird',
                metadata={'completion_time': datetime.utcnow()}
            )
        elif 21 <= hour < 24:
            await momentum_service.process_event(
                user_id=time_slot.owner_id,
                event_type='night_owl',
                metadata={'completion_time': datetime.utcnow()}
            )
    
    db.commit()
    db.refresh(time_slot)
    return time_slot