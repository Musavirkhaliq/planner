from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_db
from ..auth.dependencies import get_current_user
from . import services
from . import schemas
from ..users.schemas import User
from ..models import Goal, GoalStep

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

@router.patch("/{goal_id}", response_model=schemas.Goal)
async def update_goal(
    goal_id: int,
    goal_update: schemas.GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_goal = services.get_goal(db, goal_id=goal_id, user_id=current_user.id)
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return await services.update_goal(db=db, goal=db_goal, goal_update=goal_update)

@router.post("/{goal_id}/steps", response_model=schemas.GoalStep)
def create_goal_step(
    goal_id: int,
    step: schemas.GoalStepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify goal exists and belongs to user
    goal = services.get_goal(db, goal_id=goal_id, user_id=current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return services.create_goal_step(db=db, step=step, goal_id=goal_id)

@router.patch("/{goal_id}/steps/{step_id}", response_model=schemas.GoalStep)
async def update_goal_step(
    goal_id: int,
    step_id: int,
    step_update: schemas.GoalStepUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify goal exists and belongs to user
    goal = services.get_goal(db, goal_id=goal_id, user_id=current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Get the step
    step = db.query(GoalStep).filter(
        GoalStep.id == step_id,
        GoalStep.goal_id == goal_id
    ).first()
    
    if not step:
        raise HTTPException(status_code=404, detail="Goal step not found")
    
    return await services.update_goal_step(db=db, step=step, step_update=step_update) 