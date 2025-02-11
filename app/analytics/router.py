from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ..dependencies import get_db
from ..auth.dependencies import get_current_user
from . import services
from . import schemas
from ..users.schemas import User

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
def update_time_slot(
    slot_id: int,
    update: schemas.TimeSlotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    slot = services.get_time_slot(db, slot_id, current_user.id)
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return services.update_time_slot(db, slot, update)

# Ensure this endpoint is defined with @router.get
@router.get("/analytics", response_model=schemas.Analytics)
def get_analytics(
    start: Optional[date] = Query(None, description="Start date for analytics"),
    end: Optional[date] = Query(None, description="End date for analytics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return services.get_user_analytics(db, current_user.id, start, end)