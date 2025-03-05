# Momentum Initialization Scripts

This directory contains scripts for initializing and maintaining the momentum system data.

## Available Scripts

### `init_momentum.py`

This script initializes all momentum data (levels, achievements, streaks) for all users in the system. It is typically run once after the initial database setup or when new users are added outside the normal registration flow.

```bash
python scripts/init_momentum.py
```

### `init_levels.py`

This script specifically initializes or updates all levels in the database based on the levels defined in `app/momentum/momentum.py`. It's useful when you've modified the level definitions and need to update the database to match.

```bash
python scripts/init_levels.py
```

## When to Run These Scripts

- **After schema changes**: If you've modified the momentum data structure, run these scripts to ensure the database is in sync.
- **After adding new levels**: If you've added or modified levels in `momentum.py`, run `init_levels.py` to update the database.
- **After data corruption**: If momentum data becomes corrupted, these scripts can help restore it.

## Automatic Initialization

In the normal application flow, user momentum data is automatically initialized in these cases:
1. When a new user registers (in `app/auth/router.py`) 
2. When a user logs in (also in `app/auth/router.py`)

The levels themselves are initialized when the first user is created, but only the first 5 levels were being created. The `init_levels.py` script now ensures all 10 levels from the `momentum.py` file are properly created in the database.

## Development Notes

If you modify the `LEVELS` list in `momentum.py`, you should run the `init_levels.py` script to update the database. The system does not automatically detect changes to the level definitions. 