from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..users import services as user_services
from . import services, oauth
from ..config import settings
from typing import Optional
import time

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="frontend/templates")

# Rate limiting storage
verification_attempts = {}  # {email: [(timestamp, attempt_count)]}

def check_rate_limit(email: str) -> bool:
    """Check if email has exceeded rate limit (3 attempts per hour)"""
    now = time.time()
    hour_ago = now - 3600  # 1 hour ago
    
    # Clean up old attempts
    if email in verification_attempts:
        verification_attempts[email] = [
            (ts, count) for ts, count in verification_attempts[email] 
            if ts > hour_ago
        ]
    
    # Count recent attempts
    attempts = verification_attempts.get(email, [])
    recent_attempts = sum(count for ts, count in attempts if ts > hour_ago)
    
    return recent_attempts < 3

def add_verification_attempt(email: str):
    """Record a verification attempt"""
    now = time.time()
    if email not in verification_attempts:
        verification_attempts[email] = []
    verification_attempts[email].append((now, 1))

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_services.get_user_by_email(db, email=form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not services.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # If email is not verified, redirect to verification page
    if not user.is_email_verified:
        return JSONResponse(
            content={"message": "verify_email", "email": user.email},
            status_code=200
        )
    
    access_token = services.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(request: Request, email: str):
    return templates.TemplateResponse(
        "verify_email.html",
        {"request": request, "email": email}
    )

@router.post("/send-verification")
async def send_verification(email: str, db: Session = Depends(get_db)):
    user = user_services.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check rate limit
    if not check_rate_limit(email):
        raise HTTPException(
            status_code=429, 
            detail="Too many verification attempts. Please try again in an hour."
        )
    
    verification = user_services.create_email_verification(db, email)
    success = await user_services.send_verification_email(
        email=email,
        name=email.split("@")[0],
        otp=verification.otp
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send verification email")
    
    # Record the attempt
    add_verification_attempt(email)
    
    return {"message": "Verification email sent"}

@router.post("/verify-otp")
async def verify_otp(
    email: str = Form(...),
    otp: str = Form(...),
    db: Session = Depends(get_db)
):
    if user_services.verify_otp(db, email, otp):
        return {"message": "Email verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid or expired OTP")

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