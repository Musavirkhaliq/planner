from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Task
from .schemas import TaskCreate, TaskUpdate
from datetime import datetime
from ..momentum.services import MomentumService

def get_tasks(db: Session, user_id: int):
    return db.query(Task).filter(Task.owner_id == user_id).all()

def get_task(db: Session, task_id: int, user_id: int):
    return db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()

def create_task(db: Session, task: TaskCreate, user_id: int):
    db_task = Task(**task.dict(), owner_id=user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

async def update_task(db: Session, task: Task, task_update: TaskUpdate):
    old_completed = task.completed
    
    # Update task fields
    if task_update.completed is not None:
        task.completed = task_update.completed
    if task_update.time_spent is not None:
        task.time_spent = task_update.time_spent
    
    momentum_service = MomentumService(db)
    
    # Check if task was uncompleted
    if old_completed and task_update.completed is False:
        # Revert task completion event
        await momentum_service.revert_event(
            user_id=task.owner_id,
            event_type='task_completion',
            metadata={
                'task_id': task.id,
                'completion_time': datetime.utcnow(),
                'is_weekend': datetime.utcnow().weekday() >= 5,
                'complexity': getattr(task, 'complexity', 1)  # Default to 1 if complexity not set
            }
        )
        
        # If this was completed on a weekend, also revert weekend warrior bonus
        if getattr(task, 'completed_at', None) and task.completed_at.weekday() >= 5:
            await momentum_service.revert_event(
                user_id=task.owner_id,
                event_type='weekend_warrior',
                metadata={
                    'completion_time': task.completed_at
                }
            )
    
    # Check if task was just completed
    elif task.completed and not old_completed:
        # Check if this is the first task completed today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        completed_today = db.query(Task).filter(
            Task.owner_id == task.owner_id,
            Task.completed == True,
            func.date(Task.updated_at) == func.date(datetime.utcnow())
        ).count()
        
        is_first_task = completed_today == 0
        
        # Process task completion event
        await momentum_service.process_event(
            user_id=task.owner_id,
            event_type='task_completion',
            metadata={
                'task_id': task.id,
                'completion_time': datetime.utcnow(),
                'is_weekend': datetime.utcnow().weekday() >= 5,
                'is_first_task': is_first_task,
                'complexity': getattr(task, 'complexity', 1)  # Default to 1 if complexity not set
            }
        )
        
        # Award first task of day bonus if applicable
        if is_first_task:
            await momentum_service.process_event(
                user_id=task.owner_id,
                event_type='first_task_of_day',
                metadata={
                    'completion_time': datetime.utcnow()
                }
            )
        
        # Award weekend warrior bonus if applicable
        if datetime.utcnow().weekday() >= 5:
            await momentum_service.process_event(
                user_id=task.owner_id,
                event_type='weekend_warrior',
                metadata={
                    'completion_time': datetime.utcnow()
                }
            )
    
    db.commit()
    db.refresh(task)
    return task 