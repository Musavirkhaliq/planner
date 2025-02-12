from sqlalchemy.orm import Session
from ..models import User, EmailVerification
from ..utils import get_password_hash
from .schemas import UserCreate
from datetime import datetime, timedelta
import random
import string
import httpx

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def generate_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))


async def send_verification_email(email: str, name: str, otp: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://util.mhbhat.in/send_otp_mail.php',  # Update URL as needed
                data={  # Use the `data` parameter to send form-encoded data
                    'email_to': email,
                    'name': name,
                    'otp': otp
                }
            )
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def create_email_verification(db: Session, email: str) -> EmailVerification:
    # Delete any existing unused verifications for this email
    db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.is_used == False
    ).delete()
    
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=15)  # OTP expires in 15 minutes
    
    verification = EmailVerification(
        email=email,
        otp=otp,
        expires_at=expires_at
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification

def verify_otp(db: Session, email: str, otp: str) -> bool:
    verification = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.otp == otp,
        EmailVerification.is_used == False,
        EmailVerification.expires_at > datetime.utcnow()
    ).first()
    
    if verification:
        # Mark OTP as used
        verification.is_used = True
        # Mark user as verified
        user = get_user_by_email(db, email)
        if user:
            user.is_email_verified = True
        db.commit()
        return True
    return False

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_email_verified=False  # New users start unverified
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user 