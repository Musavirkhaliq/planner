# Momentum Initialization Scripts

This directory contains scripts for initializing and maintaining the momentum system data.

## Available Scripts

### `init_momentum.py`

This script initializes all momentum data (levels, achievements, streaks) for all users in the system. It is typically run once after the initial database setup or when new users are added outside the normal registration flow.

**Note:** This script may encounter SQLAlchemy model errors due to circular imports. If that happens, use `init_momentum_direct.py` instead.

```bash
python scripts/init_momentum.py
```

### `init_momentum_direct.py`

This is an improved version of `init_momentum.py` that uses direct SQLite commands instead of SQLAlchemy ORM to avoid model initialization errors. It performs the same function as `init_momentum.py` but is more reliable.

```bash
python scripts/init_momentum_direct.py
```

### `init_levels.py`

This script specifically initializes or updates all levels in the database based on the levels defined in `app/momentum/momentum.py`. It's useful when you've modified the level definitions and need to update the database to match.

```bash
python scripts/init_levels.py
```

### `rollback_momentum.py`

This script allows you to roll back or reset momentum features in various ways. It provides multiple options to handle different rollback scenarios, from resetting individual user progress to completely purging all momentum data.

```bash
# Show help with all available options
python scripts/rollback_momentum.py --help

# Create a backup before making any changes
python scripts/rollback_momentum.py --backup --reset-points

# Reset a specific user's momentum progress
python scripts/rollback_momentum.py --user-id 1 --reset-all-users

# Reset all levels to the default configuration in momentum.py
python scripts/rollback_momentum.py --reset-default-levels

# Complete purge of all momentum data (with confirmation prompt)
python scripts/rollback_momentum.py --purge --keep-structure
```

Available options:
- `--backup`: Create a backup of all momentum data before making changes
- `--user-id ID`: Specify a user ID to only affect that user
- `--reset-points`: Reset points to zero
- `--reset-levels`: Reset users to level 1
- `--reset-achievements`: Reset achievement progress to zero
- `--reset-streaks`: Reset streaks to zero
- `--reset-default-levels`: Reset levels to default configuration from momentum.py
- `--purge`: Completely purge all momentum data (requires confirmation)
- `--keep-structure`: When purging, keep table structure but delete all data
- `--reset-all-users`: Reset all user momentum progress (points, level, achievements, streaks)

## When to Run These Scripts

- **After schema changes**: If you've modified the momentum data structure, run these scripts to ensure the database is in sync.
- **After adding new levels**: If you've added or modified levels in `momentum.py`, run `init_levels.py` to update the database.
- **After data corruption**: If momentum data becomes corrupted, these scripts can help restore it.
- **When encountering model errors**: If you get SQLAlchemy model errors with `init_momentum.py`, use `init_momentum_direct.py` instead.
- **When rolling back changes**: If you need to roll back momentum features, use `rollback_momentum.py` with appropriate options.

## Automatic Initialization

In the normal application flow, user momentum data is automatically initialized in these cases:
1. When a new user registers (in `app/auth/router.py`) 
2. When a user logs in (also in `app/auth/router.py`)

The levels themselves are initialized when the first user is created, but only the first 5 levels were being created. The `init_levels.py` script now ensures all 10 levels from the `momentum.py` file are properly created in the database.

## Troubleshooting

If you encounter an error like this:
```
Error initializing momentum data: When initializing mapper Mapper[User(users)], expression 'Reflection' failed to locate a name ('Reflection').
```

This is an SQLAlchemy model initialization error often caused by circular imports. Use the direct SQLite scripts (`init_momentum_direct.py` or `init_levels.py`) instead, which bypass the SQLAlchemy ORM and interact directly with the database.

## Development Notes

If you modify the `LEVELS` list in `momentum.py`, you should run the `init_levels.py` script to update the database. The system does not automatically detect changes to the level definitions. 