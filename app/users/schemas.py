from pydantic import BaseModel, EmailStr, constr

class UserBase(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")  # Alphanumeric with _ and -

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True
    is_email_verified: bool = False

    class Config:
        from_attributes = True 