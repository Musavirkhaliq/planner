from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from ..config import settings
from ..users import services as user_services
from .schemas import UserLogin, TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def create_token(user) -> dict:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

async def authenticate_user(db: Session, user_credentials: UserLogin):
    user = user_services.get_user_by_email(db, email=user_credentials.email)
    if not user:
        return None
    if not verify_password(user_credentials.password, user.hashed_password):
        return None
    return user

async def create_user(db: Session, user_data):
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create the user
    db_user = user_services.create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    return db_user 