from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from ..dependencies import get_db
from ..auth.dependencies import get_current_user
from . import services
from . import schemas
from ..users.schemas import User
from ..models import TimeSlot
from ..momentum.services import MomentumService


router = APIRouter(prefix="/time_slots", tags=["time_slots"])

@router.get("/", response_model=List[schemas.TimeSlot])
def read_time_slots(
    date: Optional[date] = Query(None, description="Filter time slots by date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return services.get_time_slots(db=db, user_id=current_user.id, date=date)

@router.post("/", response_model=schemas.TimeSlot)
def create_time_slot(
    time_slot: schemas.TimeSlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return services.create_time_slot(db=db, time_slot=time_slot, owner_id=current_user.id)

@router.patch("/{slot_id}", response_model=schemas.TimeSlot)
async def update_time_slot(
    slot_id: int,
    update: schemas.TimeSlotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    slot = services.get_time_slot(db, slot_id, current_user.id)
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return await services.update_time_slot(db, slot, update)

@router.put("/{slot_id}", response_model=schemas.TimeSlot)
async def update_time_slot(
    slot_id: int,
    slot_update: schemas.TimeSlotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if time slot exists and belongs to current user
    db_slot = db.query(TimeSlot).filter(
        TimeSlot.id == slot_id,
        TimeSlot.owner_id == current_user.id
    ).first()
    
    if not db_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found"
        )
    
    return await services.update_time_slot(db, db_slot, slot_update)

# Delete time slot endpoint
@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if time slot exists and belongs to current user
    db_slot = db.query(TimeSlot).filter(
        TimeSlot.id == slot_id,
        TimeSlot.owner_id == current_user.id
    ).first()
    
    if not db_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found"
        )
    
    try:
        # If the time slot was completed, we need to revert the points
        if db_slot.status == "completed":
            momentum_service = MomentumService(db)
            
            # Calculate duration in minutes
            duration = int((db_slot.end_time - db_slot.start_time).total_seconds() / 60)
            
            # Revert time slot completion event
            await momentum_service.revert_event(
                user_id=db_slot.owner_id,
                event_type='time_slot_completion',
                metadata={
                    'duration': duration,
                    'completion_time': db_slot.updated_at or datetime.utcnow(),
                    'is_weekend': (db_slot.updated_at or datetime.utcnow()).weekday() >= 5
                }
            )
            
            # If it was a focused session, revert that too
            if duration >= 25:
                await momentum_service.revert_event(
                    user_id=db_slot.owner_id,
                    event_type='focused_session',
                    metadata={
                        'duration': duration,
                        'completion_time': db_slot.updated_at or datetime.utcnow()
                    }
                )
        
        # Now delete the time slot
        db.delete(db_slot)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )