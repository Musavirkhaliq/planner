from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from .users import services as user_services
from .dependencies import get_db

from sqlalchemy.orm import Session

router = APIRouter(tags=["web"])

templates = Jinja2Templates(directory="frontend/templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def read_login(request: Request, error: Optional[str] = Query(None)):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@router.get("/register", response_class=HTMLResponse)
async def read_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/verify-email", response_class=HTMLResponse)
async def read_verify_email(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    # Check if the user exists and is not verified
    user = user_services.get_user_by_email(db, email=email)
    if not user:
        return RedirectResponse(url="/register")
    if user.is_email_verified:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "verify_email.html", 
        {"request": request, "email": email}
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request}) 

@router.get("/analytics", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request}) 

@router.get("/momentum", response_class=HTMLResponse)
async def momentum_page(request: Request):
    """Render the momentum profile page"""
    return templates.TemplateResponse(
        "momentum.html",
        {"request": request}
    ) 