from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_db
from ..auth.dependencies import get_current_user
from . import services
from . import schemas
from ..users.schemas import User

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=schemas.Task)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return services.create_task(db=db, task=task, user_id=current_user.id)

@router.get("/", response_model=List[schemas.Task])
def read_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return services.get_tasks(db=db, user_id=current_user.id)

@router.patch("/{task_id}", response_model=schemas.Task)
async def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_task = services.get_task(db, task_id=task_id, user_id=current_user.id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return await services.update_task(db=db, task=db_task, task_update=task_update)

@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if task exists and belongs to current user
    from ..models import Task
    db_task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == current_user.id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # If the task was completed, we need to revert the points
        if db_task.completed:
            from ..momentum.services import MomentumService
            from datetime import datetime
            
            momentum_service = MomentumService(db)
            
            # Revert task completion event
            await momentum_service.revert_event(
                user_id=db_task.owner_id,
                event_type='task_completion',
                metadata={
                    'task_id': db_task.id,
                    'completion_time': db_task.updated_at or datetime.utcnow(),
                    'is_weekend': (db_task.updated_at or datetime.utcnow()).weekday() >= 5,
                    'complexity': getattr(db_task, 'complexity', 1)  # Default to 1 if complexity not set
                }
            )
        
        # Now delete the task
        db.delete(db_task)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) 