# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from . import models, database
from .web_router import router as web_router
from .api_router import router as api_router
from .analytics.router import router as analytics_router
from .tafakur.router import router as tafakur_router

from .config import settings

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://planner.sukoonsphere.org",
        "http://localhost:9000",
        "http://127.0.0.1:9000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware - required for OAuth
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Mount static files
# app.mount("/templates", StaticFiles(directory="frontend/templates"), name="templates")

# Include routers
app.include_router(web_router)
app.include_router(api_router)
app.include_router(analytics_router)
app.include_router(tafakur_router, prefix="/api")

# The momentum scheduler has been moved to an external system (systemd timer or cron)
# See the following files for details:
#  - /scripts/run_momentum_checks.py - The standalone script that runs the checks
#  - /systemd/momentum-checks.service - The systemd service definition
#  - /systemd/momentum-checks.timer - The systemd timer definition
#  - /scripts/momentum-crontab - The crontab entry for momentum checks

# If you need to enable the in-process scheduler (not recommended for production),
# uncomment the following:
# 
# from .momentum.scheduler import initialize_scheduler
# import asyncio
# 
# @app.on_event("startup")
# async def startup_event():
#     # Initialize the momentum scheduler
#     await initialize_scheduler()
#     print("Momentum scheduler initialized")


