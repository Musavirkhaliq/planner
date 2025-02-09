from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_db
from ..auth.dependencies import get_current_user
from . import services
from . import schemas
from ..users.schemas import User

router = APIRouter(prefix="/goals", tags=["goals"])

@router.post("/", response_model=schemas.Goal)
def create_goal(
    goal: schemas.GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return services.create_goal(db=db, goal=goal, user_id=current_user.id)

@router.get("/", response_model=List[schemas.Goal])
def read_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return services.get_goals(db=db, user_id=current_user.id)

@router.post("/{goal_id}/steps/", response_model=schemas.GoalStep)
def create_goal_step(
    goal_id: int,
    step: schemas.GoalStepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return services.create_goal_step(db=db, step=step, goal_id=goal_id) 