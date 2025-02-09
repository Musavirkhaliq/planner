# Planner Application

A FastAPI-based planner application with task management, goal tracking, and time slot scheduling features.

## Project Structure

```
app/
├── api/                    # API router aggregation
├── auth/                   # Authentication module
├── users/                  # User management module
├── tasks/                  # Task management module
├── goals/                  # Goal tracking module
├── time_slots/            # Time slot scheduling module
├── analytics/             # Analytics and reporting module
├── web/                   # Web interface routes
├── models.py              # SQLAlchemy models
├── database.py            # Database configuration
├── config.py              # Application configuration
└── dependencies.py        # Shared dependencies
```

## Features

- User authentication and authorization
- Task management with completion tracking
- Goal setting and step-by-step tracking
- Time slot scheduling and management
- Analytics and productivity metrics
- Web interface for easy access

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (optional):
Create a `.env` file in the root directory with:
```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./app.db
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the application is running, you can access:
- Interactive API documentation: http://localhost:8000/docs
- Alternative API documentation: http://localhost:8000/redoc

## Development

The project follows a modular structure where each feature has its own module containing:
- `router.py`: API endpoints
- `services.py`: Business logic
- `schemas.py`: Pydantic models for request/response validation

## Authentication

The application uses JWT-based authentication. To access protected endpoints:
1. Register a new user at `/api/users/`
2. Get a token at `/api/auth/token`
3. Use the token in the Authorization header: `Bearer <token>`