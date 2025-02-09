from sqlalchemy.orm import Session
from ..models import Task

def get_user_analytics(db: Session, user_id: int):
    tasks = db.query(Task).filter(Task.owner_id == user_id).all()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.completed)
    total_time = sum(t.time_spent for t in tasks)
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "total_time_spent": total_time,
    } 