from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

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
async def read_verify_email(request: Request, email: str):
    return templates.TemplateResponse(
        "verify_email.html", 
        {"request": request, "email": email}
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request}) 