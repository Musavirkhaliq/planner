from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Goal, GoalStep
from .schemas import GoalCreate, GoalUpdate, GoalStepCreate, GoalStepUpdate
from datetime import datetime
from ..momentum.services import MomentumService

def get_goals(db: Session, user_id: int):
    return db.query(Goal).filter(Goal.owner_id == user_id).all()

def get_goal(db: Session, goal_id: int, user_id: int):
    return db.query(Goal).filter(Goal.id == goal_id, Goal.owner_id == user_id).first()

def create_goal(db: Session, goal: GoalCreate, user_id: int):
    db_goal = Goal(**goal.dict(), owner_id=user_id)
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

async def update_goal(db: Session, goal: Goal, goal_update: GoalUpdate):
    old_completed = goal.completed
    
    # Update goal fields
    for key, value in goal_update.dict(exclude_unset=True).items():
        setattr(goal, key, value)
    
    # Check if goal was just completed
    if goal.completed and not old_completed:
        momentum_service = MomentumService(db)
        
        # Get goal streak information
        goals_streak = await _get_goal_streak(db, goal.owner_id)
        
        # Process goal completion event
        await momentum_service.process_event(
            user_id=goal.owner_id,
            event_type='goal_completion',
            metadata={
                'goal_id': goal.id,
                'completion_time': datetime.utcnow(),
                'is_weekend': datetime.utcnow().weekday() >= 5,
                'current_streak': goals_streak
            }
        )
        
        # Process goal streak event if applicable
        if goals_streak > 0:
            await momentum_service.process_event(
                user_id=goal.owner_id,
                event_type='goal_streak',
                metadata={
                    'streak': goals_streak,
                    'completion_time': datetime.utcnow()
                }
            )
    
    db.commit()
    db.refresh(goal)
    return goal

async def update_goal_step(db: Session, step: GoalStep, step_update: GoalStepUpdate):
    old_completed = step.completed
    
    # Update step fields
    for key, value in step_update.dict(exclude_unset=True).items():
        setattr(step, key, value)
    
    # Check if step was just completed
    if step.completed and not old_completed:
        momentum_service = MomentumService(db)
        
        # Process goal step completion event
        await momentum_service.process_event(
            user_id=step.goal.owner_id,  # Assuming goal relationship is set up
            event_type='goal_step_completion',
            metadata={
                'step_id': step.id,
                'goal_id': step.goal_id,
                'completion_time': datetime.utcnow(),
                'is_weekend': datetime.utcnow().weekday() >= 5
            }
        )
    
    db.commit()
    db.refresh(step)
    return step

async def _get_goal_streak(db: Session, user_id: int) -> int:
    """Helper function to calculate the current goal completion streak"""
    goals = db.query(Goal).filter(
        Goal.owner_id == user_id,
        Goal.completed == True
    ).order_by(Goal.completed_at.desc()).all()
    
    if not goals:
        return 0
    
    streak = 1
    last_completion = goals[0].completed_at.date()
    
    for goal in goals[1:]:
        current_completion = goal.completed_at.date()
        if (last_completion - current_completion).days == 1:
            streak += 1
            last_completion = current_completion
        else:
            break
    
    return streak

def create_goal_step(db: Session, step: GoalStepCreate, goal_id: int):
    db_step = GoalStep(**step.dict(), goal_id=goal_id)
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step 