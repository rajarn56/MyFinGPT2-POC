# Test Suite

Test suite for MyFinGPT-POC-V2.

## Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for component interactions
├── e2e/            # End-to-end tests for complete workflows
├── fixtures/       # Test fixtures and mock data
└── helpers/        # Test helper functions and utilities
```

## Running Tests

### All Tests
```bash
# From project root
cd backend
pytest tests/ -v
```

### Specific Test Types
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v
```

### With Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Organization

- **Unit Tests**: Test individual functions, classes, and methods in isolation
- **Integration Tests**: Test interactions between components (e.g., database clients, API endpoints)
- **E2E Tests**: Test complete user workflows from API request to response

## Test Fixtures

Common fixtures are stored in `tests/fixtures/` and can be imported in test files.

## Test Helpers

Helper functions for common test operations are in `tests/helpers/`.

## Phase Status

- ✅ **Phase 0**: Test structure created
- ⏳ **Phase 2+**: Tests will be implemented alongside features
