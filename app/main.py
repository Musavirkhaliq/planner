# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from . import crud, models, schemas, auth
from fastapi.security import OAuth2PasswordRequestForm
from .dependencies import get_db

from app import models, database
models.Base.metadata.create_all(bind=database.engine)
from typing import Optional


app = FastAPI()



# Mount static files and templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Root endpoints to serve pages
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def read_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Login endpoint: now actually checks the password!
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Task endpoints: creation, reading, and updating (time spent and completion)
@app.post("/tasks/", response_model=schemas.Task)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    return crud.create_task(db=db, task=task, user_id=current_user.id)

@app.get("/tasks/", response_model=list[schemas.Task])
def read_tasks(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    return crud.get_tasks(db=db, user_id=current_user.id)

@app.patch("/tasks/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,  # see schemas update below
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    db_task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return crud.update_task(db=db, task=db_task, task_update=task_update)

# Goal endpoints (creation, reading, and adding steps)
@app.post("/goals/", response_model=schemas.Goal)
def create_goal(
    goal: schemas.GoalCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    return crud.create_goal(db=db, goal=goal, user_id=current_user.id)

@app.get("/goals/", response_model=list[schemas.Goal])
def read_goals(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    return crud.get_goals(db=db, user_id=current_user.id)

@app.post("/goals/{goal_id}/steps/", response_model=schemas.GoalStep)
def create_goal_step(
    goal_id: int,
    step: schemas.GoalStepCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    return crud.create_goal_step(db=db, step=step, goal_id=goal_id)

# Time Slot endpoints (for booking and reading slots)
@app.post("/time_slots/", response_model=schemas.TimeSlot)
def create_time_slot(
    time_slot: schemas.TimeSlotCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    return crud.create_time_slot(db=db, time_slot=time_slot, owner_id=current_user.id)

@app.get("/time_slots/", response_model=list[schemas.TimeSlot])
def read_time_slots(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    return crud.get_time_slots(db=db, user_id=current_user.id)

# Analytics endpoint: returns productivity metrics (e.g. total tasks and hours spent)
@app.get("/analytics/")
def get_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    tasks = crud.get_tasks(db=db, user_id=current_user.id)
    time_slots = crud.get_time_slots(db=db, user_id=current_user.id)

    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        tasks = [task for task in tasks if start_date <= task.created_at <= end_date]
        time_slots = [slot for slot in time_slots if start_date <= slot.date <= end_date]

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.completed)
    total_time = sum(t.time_spent for t in tasks)
    total_time_slots = len(time_slots)
    completed_time_slots = sum(1 for slot in time_slots if slot.done)

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "total_time_spent": total_time,
        "total_time_slots": total_time_slots,
        "completed_time_slots": completed_time_slots,
    }

# Stub: Customizable Dashboard Settings
@app.post("/dashboard/settings")
def update_dashboard_settings(
    settings: schemas.DashboardSettings,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    # In a full implementation, save settings (theme, layout, etc.) in the DB.
    return {"msg": "Settings updated", "settings": settings}

@app.get("/time_slots/by_date/")
def get_time_slots_by_date(
    date: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    date = datetime.strptime(date, "%Y-%m-%d").date()
    time_slots = crud.get_time_slots_by_date(db=db, user_id=current_user.id, date=date)
    return time_slots

@app.patch("/time_slots/{slot_id}", response_model=schemas.TimeSlot)
def patch_time_slot(
    slot_id: int,
    update: schemas.TimeSlotUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    slot = crud.get_time_slot(db, slot_id, current_user.id)
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return crud.update_time_slot(db, slot, update)

