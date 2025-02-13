from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
import httpx
from sqlalchemy.orm import Session
from ..config import settings
from ..users import services as user_services, schemas
import secrets

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url=settings.GOOGLE_CONF_URL,
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'
    },
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    authorize_params={
        'access_type': 'offline'  # Enable refresh token
    }
)

async def google_oauth_init(request: Request):
    try:
        # Construct the callback URL to match Google OAuth settings
        base_url = str(request.base_url).rstrip('/')
        redirect_uri = f"{base_url}/api/auth/callback"
        
        print(f"Redirect URI: {redirect_uri}")  # Debug print
        
        # Force http for local development if needed
        if not request.url.is_secure:
            redirect_uri = redirect_uri.replace('https://', 'http://')
        
        return await oauth.google.authorize_redirect(
            request,
            redirect_uri,
            access_type='offline'  # Request refresh token
        )
    except Exception as e:
        print(f"Error in google_oauth_init: {str(e)}")
        raise

async def get_google_oauth_token(request: Request):
    try:
        # Debug print the request URL
        print(f"Callback URL: {request.url}")
        
        # Get the token
        token = await oauth.google.authorize_access_token(request)
        if not token:
            print("No token received from Google")
            raise HTTPException(status_code=400, detail="No token received from Google")
        
        print(f"Received token: {token.keys()}")  # Debug print token keys
        
        # Get user info using the access token
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {token["access_token"]}'}
            response = await client.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
            
            if response.status_code != 200:
                print(f"Failed to get user info. Status: {response.status_code}")
                raise HTTPException(status_code=400, detail="Failed to get user info from Google")
            
            user_info = response.json()
            print(f"User info received: {user_info}")  # Debug print
            
            if not user_info or 'email' not in user_info:
                raise HTTPException(status_code=400, detail="Invalid user info received from Google")
            
            return user_info
            
    except Exception as e:
        print(f"Error in get_google_oauth_token: {str(e)}")
        if 'token' in locals():
            print(f"Token data: {token}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

async def get_or_create_user_from_google(db: Session, google_user: dict):
    email = google_user.get('email')
    if not email:
        raise HTTPException(status_code=400, detail="Invalid Google user data")
    
    user = user_services.get_user_by_email(db, email=email)
    if not user:
        # Create new user with random password since they'll use Google login
        random_pass = secrets.token_urlsafe(32)
        # get first part of email as username
        username = email.split('@')[0]
        user_create = schemas.UserCreate(email=email, password=random_pass, username=username)
        user = user_services.create_user(db=db, user=user_create)
    
    return user 