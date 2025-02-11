# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from . import models, database
from .web_router import router as web_router
from .api_router import router as api_router
from .time_slots.router import router as time_slots_router

from .config import settings

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Add session middleware - required for OAuth
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Mount static files
app.mount("/templates", StaticFiles(directory="frontend/templates"), name="templates")

# Include routers
app.include_router(web_router)
app.include_router(api_router)
app.include_router(time_slots_router)
