from sqlalchemy.orm import Session
from ..models import Goal, GoalStep
from .schemas import GoalCreate, GoalStepCreate

def get_goals(db: Session, user_id: int):
    return db.query(Goal).filter(Goal.owner_id == user_id).all()

def create_goal(db: Session, goal: GoalCreate, user_id: int):
    db_goal = Goal(**goal.dict(), owner_id=user_id)
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def create_goal_step(db: Session, step: GoalStepCreate, goal_id: int):
    db_step = GoalStep(**step.dict(), goal_id=goal_id)
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step 