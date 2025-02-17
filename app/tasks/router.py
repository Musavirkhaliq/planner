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