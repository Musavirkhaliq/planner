from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User
from app.tafakur import schemas, services

router = APIRouter(
    prefix="/tafakur",
    tags=["tafakur"],
    responses={404: {"description": "Not found"}},
)

@router.post("/reflections", response_model=schemas.Reflection)
async def create_reflection(
    reflection: schemas.ReflectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new reflection for the current day"""
    tafakur_service = services.TafakurService(db)
    return await tafakur_service.create_reflection(current_user.id, reflection)

@router.get("/reflections", response_model=List[schemas.Reflection])
async def get_reflections(
    skip: int = 0,
    limit: int = 100,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reflections for the current user"""
    tafakur_service = services.TafakurService(db)
    return tafakur_service.get_reflections(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date
    )

@router.get("/reflections/today", response_model=Optional[schemas.Reflection])
async def get_today_reflection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's reflection if it exists"""
    tafakur_service = services.TafakurService(db)
    return tafakur_service.get_reflection_by_date(current_user.id, date.today())

@router.get("/reflections/date/{reflection_date}", response_model=Optional[schemas.Reflection])
async def get_reflection_by_date(
    reflection_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a reflection for a specific date"""
    tafakur_service = services.TafakurService(db)
    return tafakur_service.get_reflection_by_date(current_user.id, reflection_date)

@router.get("/reflections/{reflection_id}", response_model=schemas.Reflection)
async def get_reflection(
    reflection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific reflection by ID"""
    tafakur_service = services.TafakurService(db)
    reflection = tafakur_service.get_reflection(current_user.id, reflection_id)
    if not reflection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reflection not found"
        )
    return reflection

@router.put("/reflections/{reflection_id}", response_model=schemas.Reflection)
async def update_reflection(
    reflection_id: int,
    reflection_update: schemas.ReflectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a specific reflection"""
    tafakur_service = services.TafakurService(db)
    reflection = tafakur_service.update_reflection(
        current_user.id, 
        reflection_id, 
        reflection_update
    )
    if not reflection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reflection not found"
        )
    return reflection

@router.delete("/reflections/{reflection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reflection(
    reflection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific reflection"""
    tafakur_service = services.TafakurService(db)
    success = tafakur_service.delete_reflection(current_user.id, reflection_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reflection not found"
        )
    return None

@router.get("/streak", response_model=schemas.ReflectionStreak)
async def get_reflection_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current reflection streak information"""
    tafakur_service = services.TafakurService(db)
    return tafakur_service.get_reflection_streak(current_user.id)

@router.get("/insights", response_model=schemas.ReflectionInsight)
async def get_insights(
    from_date: Optional[date] = Query(None, description="Start date for insights analysis"),
    to_date: Optional[date] = Query(None, description="End date for insights analysis"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get insights and analytics from user's reflections"""
    tafakur_service = services.TafakurService(db)
    return tafakur_service.get_insights(
        user_id=current_user.id,
        from_date=from_date,
        to_date=to_date
    ) 