from sqlalchemy.orm import Session
from . import schemas
from .. import models
from typing import Optional
from datetime import date, timedelta, datetime, timezone
from ..momentum.services import MomentumService
from ..momentum.momentum import FOCUSED_SESSION_THRESHOLD
import pytz

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
    duration = int((time_slot.end_time - time_slot.start_time).total_seconds() / 60)
    # Check if status changed from completed to something else (task was uncompleted)
    if old_status == "completed" and update.status and update.status != "completed":
        # Revert time slot completion event
        await momentum_service.revert_event(
            user_id=time_slot.owner_id,
            event_type='time_slot_completion',
            metadata={
                'duration': duration,
                'completion_time': datetime.now(timezone.utc),
                'is_weekend': datetime.now(timezone.utc).weekday() >= 5
            }
        )
        
        # If it was a focused session, revert that too
        if duration >= FOCUSED_SESSION_THRESHOLD:
            await momentum_service.revert_event(
                user_id=time_slot.owner_id,
                event_type='focused_session',
                metadata={
                    'duration': duration,
                    'completion_time': datetime.now(timezone.utc)
                }
            )
    
    # Check if status changed to completed
    elif update.status == "completed" and old_status != "completed":
        # Process time slot completion event
        await momentum_service.process_event(
            user_id=time_slot.owner_id,
            event_type='time_slot_completion',
            metadata={
                'duration': duration,
                'completion_time': datetime.now(timezone.utc),
                'is_weekend': datetime.now(timezone.utc).weekday() >= 5
            }
        )
        
        if duration >= FOCUSED_SESSION_THRESHOLD:
            await momentum_service.process_event(
                user_id=time_slot.owner_id,
                event_type='focused_session',
                metadata={
                    'duration': duration,
                    'completion_time': datetime.now(timezone.utc)
                }
            )
        
        # Check for early bird or night owl bonus
        # Get the user object to access their timezone
        user = db.query(models.User).filter(models.User.id == time_slot.owner_id).first()
        user_timezone = pytz.timezone(user.timezone if user and user.timezone else "Asia/Kolkata")
        
        # Get current time in user's timezone
        now_utc = datetime.now(timezone.utc)
        user_local_time = now_utc.astimezone(user_timezone)
        hour = user_local_time.hour
        
        if 5 <= hour < 9:
            await momentum_service.process_event(
                user_id=time_slot.owner_id,
                event_type='early_bird',
                metadata={'completion_time': user_local_time}
            )
        elif 21 <= hour < 24:
            await momentum_service.process_event(
                user_id=time_slot.owner_id,
                event_type='night_owl',
                metadata={'completion_time': user_local_time}
            )
    
    db.commit()
    db.refresh(time_slot)
    return time_slot