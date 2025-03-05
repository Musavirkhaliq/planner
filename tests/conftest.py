import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
import uuid

from app.main import app
from app import models
from app.database import Base, engine
from app.config import settings

# Testing database URL - using SQLite in-memory
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create tables for test database"""
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after tests (optional: drop tables)
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a new database session for a test"""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client using the test database"""
    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Apply the overridden dependency
    from app.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    # Return a test client instance
    with TestClient(app) as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user"""
    # Generate a unique username with UUID
    unique_suffix = str(uuid.uuid4())[:8]
    username = f"testuser_{unique_suffix}"
    email = f"test_{unique_suffix}@example.com"
    
    user = models.User(
        email=email,
        username=username,
        hashed_password="$2b$12$NuE7QgQVL7SggAIC8OJmau85oR5GW0oTFVJLO2GYWE5OLaSXRI7qW",  # password: testpassword
        is_active=True,
        is_email_verified=True,
        current_level_id=None,  # Simulating a user created before momentum module (no level assigned)
        created_at=datetime.utcnow() - timedelta(days=30)  # Created 30 days ago
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_user_with_momentum(db_session, test_user):
    """Create a test user with momentum data initialized"""
    from app.momentum.init_momentum import init_user_momentum
    import asyncio
    asyncio.run(init_user_momentum(db_session, test_user.id))
    db_session.refresh(test_user)
    return test_user

@pytest.fixture(scope="function")
def additional_users(db_session):
    """Create additional test users with varying characteristics"""
    # Generate unique usernames with UUID
    suffix1 = str(uuid.uuid4())[:8]
    suffix2 = str(uuid.uuid4())[:8]
    suffix3 = str(uuid.uuid4())[:8]
    
    # User with momentum already initialized
    user1 = models.User(
        email=f"user1_{suffix1}@example.com",
        username=f"user1_{suffix1}",
        hashed_password="$2b$12$NuE7QgQVL7SggAIC8OJmau85oR5GW0oTFVJLO2GYWE5OLaSXRI7qW",
        is_active=True,
        is_email_verified=True,
        total_points=100,
        weekly_points=50,
        monthly_points=75,
        created_at=datetime.utcnow() - timedelta(days=60)
    )
    
    # Inactive user
    user2 = models.User(
        email=f"user2_{suffix2}@example.com",
        username=f"user2_{suffix2}",
        hashed_password="$2b$12$NuE7QgQVL7SggAIC8OJmau85oR5GW0oTFVJLO2GYWE5OLaSXRI7qW",
        is_active=False,
        is_email_verified=True,
        total_points=None,
        weekly_points=None,
        monthly_points=None,
        created_at=datetime.utcnow() - timedelta(days=15)
    )
    
    # New user (created recently)
    user3 = models.User(
        email=f"user3_{suffix3}@example.com",
        username=f"user3_{suffix3}",
        hashed_password="$2b$12$NuE7QgQVL7SggAIC8OJmau85oR5GW0oTFVJLO2GYWE5OLaSXRI7qW",
        is_active=True,
        is_email_verified=True,
        total_points=None,
        weekly_points=None,
        monthly_points=None,
        created_at=datetime.utcnow() - timedelta(days=1)
    )
    
    db_session.add_all([user1, user2, user3])
    db_session.commit()
    for user in [user1, user2, user3]:
        db_session.refresh(user)
    
    return [user1, user2, user3]

@pytest.fixture(scope="function")
def user_with_reflection(db_session, test_user_with_momentum):
    """Create a test user with a reflection"""
    from app.tafakur.models import Reflection, ReflectionTag
    
    reflection = Reflection(
        user_id=test_user_with_momentum.id,
        reflection_date=date.today(),
        mood="Good",
        highlights="Test highlights",
        challenges="Test challenges",
        gratitude="Test gratitude",
        lessons="Test lessons",
        tomorrow_goals="Test goals for tomorrow",
        private=False
    )
    
    db_session.add(reflection)
    db_session.flush()  # Get the ID without committing
    
    # Add tags
    tag1 = ReflectionTag(reflection_id=reflection.id, tag_name="test")
    tag2 = ReflectionTag(reflection_id=reflection.id, tag_name="fixture")
    db_session.add_all([tag1, tag2])
    
    db_session.commit()
    db_session.refresh(reflection)
    
    return test_user_with_momentum, reflection

# Create a fixture for authenticated test client
@pytest.fixture(scope="function")
def authenticated_client(client, test_user_with_momentum, db_session):
    """Create an authenticated test client"""
    # Make sure the test user is attached to the current session
    # and properly saved in the database
    db_session.add(test_user_with_momentum)
    db_session.commit()
    db_session.refresh(test_user_with_momentum)
    
    # Override get_current_user to return our test user
    async def override_get_current_user():
        # Get the user from the database to ensure it's the same session
        user = db_session.query(models.User).filter(models.User.id == test_user_with_momentum.id).first()
        if not user:
            # If user doesn't exist in this session, add it again
            db_session.add(test_user_with_momentum)
            db_session.commit()
            user = test_user_with_momentum
        return user
    
    # Import the module where get_current_user is defined
    from app.auth.dependencies import get_current_user
    from app.main import app
    
    # Override the dependency
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield client
    
    # Clean up
    app.dependency_overrides.pop(get_current_user) 