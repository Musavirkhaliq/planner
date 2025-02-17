from fastapi import APIRouter
from .users.router import router as users_router
from .tasks.router import router as tasks_router
from .goals.router import router as goals_router
from .time_slots.router import router as time_slots_router
# from .analytics.router import router as analytics_router
from .auth.router import router as auth_router
from .momentum.router import router as momentum_router

router = APIRouter(prefix="/api")

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(tasks_router)
router.include_router(goals_router)
router.include_router(time_slots_router)
router.include_router(momentum_router)
# router.include_router(analytics_router)
