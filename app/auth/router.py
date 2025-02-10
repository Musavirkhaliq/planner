from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..users import services as user_services
from . import services, oauth
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="frontend/templates")

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_services.get_user_by_email(db, email=form_data.username)
    if not user or not services.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = services.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get('/login/google')
async def google_login(request: Request):
    return await oauth.google_oauth_init(request)

@router.get('/callback')
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        print("Auth callback received. Starting Google token retrieval...")
        
        google_user = await oauth.get_google_oauth_token(request)
        print(f"Google user data received: {google_user}")
        
        user = await oauth.get_or_create_user_from_google(db, google_user)
        print(f"User retrieved/created with email: {user.email}")
        
        # Create access token
        access_token = services.create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Return the callback template with the token data
        return templates.TemplateResponse(
            "callback.html",
            {
                "request": request,
                "access_token": access_token,
                "token_type": "bearer"
            }
        )
        
    except Exception as e:
        import traceback
        print(f"Error during Google authentication: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        return templates.TemplateResponse(
            "callback.html",
            {
                "request": request,
                "detail": str(e)
            },
            status_code=400
        ) 