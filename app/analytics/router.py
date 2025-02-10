from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..auth.dependencies import get_current_user
from . import services
from . import schemas
from ..users.schemas import User

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/", response_model=schemas.Analytics)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return services.get_user_analytics(db=db, user_id=current_user.id) 