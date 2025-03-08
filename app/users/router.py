from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db
from . import services
from . import schemas
from ..auth.dependencies import get_current_user
from ..models import User
import pytz

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if email exists
    db_user = services.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    db_user = services.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    return services.create_user(db=db, user=user)

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = services.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.patch("/timezone", response_model=schemas.User)
def update_timezone(
    timezone_update: schemas.UserTimezoneUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's timezone"""
    updated_user = services.update_user_timezone(
        db=db, 
        user_id=current_user.id,
        timezone=timezone_update.timezone
    )
    
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    return updated_user 

@router.get("/timezones", response_model=list)
def get_timezones():
    """Return a list of all available timezone strings"""
    return pytz.all_timezones 