from sqlalchemy.orm import Session
from ..models import Task
from .schemas import TaskCreate, TaskUpdate

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

def update_task(db: Session, task: Task, task_update: TaskUpdate):
    if task_update.completed is not None:
        task.completed = task_update.completed
    if task_update.time_spent is not None:
        task.time_spent = task_update.time_spent
    db.commit()
    db.refresh(task)
    return task 