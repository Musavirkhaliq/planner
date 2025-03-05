# Tests for Planner App

This directory contains tests for the Planner application, with specific focus on the Momentum and Tafakur modules.

## Test Structure

The tests are organized by module:

- `tests/momentum/`: Tests for the Momentum module
- `tests/tafakur/`: Tests for the Tafakur module
- `tests/conftest.py`: Shared fixtures and test setup

## Running Tests

To run all tests:

```bash
source venv/bin/activate
pytest
```

To run tests for a specific module:

```bash
# Run all Momentum tests
pytest tests/momentum/

# Run all Tafakur tests
pytest tests/tafakur/
```

To run tests with specific markers:

```bash
# Run tests for handling pre-existing users
pytest -m pre_existing

# Run API tests
pytest -m api

# Run service layer tests
pytest -m service
```

## Test Coverage

To run tests with coverage:

```bash
pip install pytest-cov
pytest --cov=app tests/
```

To generate an HTML coverage report:

```bash
pytest --cov=app --cov-report=html tests/
```

The report will be available in the `htmlcov` directory.

## Initialization Script Tests

To specifically test the initialization script for pre-existing users:

```bash
pytest tests/momentum/test_init_momentum.py
pytest tests/momentum/test_pre_existing_users.py
```

## Notes for Developers

When adding new tests:

1. Add appropriate markers to your test functions (see pytest.ini for available markers)
2. Use the fixtures defined in conftest.py when possible
3. For tests that interact with the database, ensure you're using the test database
4. Mock external dependencies when necessary

## Troubleshooting

If you encounter errors like "Module not found", ensure you're running pytest from the project root and have all dependencies installed:

```bash
pip install -r requirements.txt
pip install pytest pytest-cov
``` 