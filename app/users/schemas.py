from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    total_points: Optional[int] = 0
    weekly_points: Optional[int] = 0
    monthly_points: Optional[int] = 0
    current_level_id: Optional[int] = None

    class Config:
        from_attributes = True 