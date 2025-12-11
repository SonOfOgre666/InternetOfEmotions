# Unit Tests for Internet of Emotions Backend Services

This directory contains comprehensive unit tests for all microservices in the Internet of Emotions backend.

## Overview

Each service has a `test_app.py` file that contains unit tests covering:
- Health endpoints
- Core business logic
- API endpoints
- Database operations
- RabbitMQ integration
- Error handling
- Edge cases

## Test Files

```
backend/services/
├── api_gateway/test_app.py          # API Gateway proxy and routing tests
├── ml_analyzer/test_app.py          # ML emotion analysis tests
├── post_fetcher/test_app.py         # Reddit post fetching tests
├── country_aggregation/test_app.py  # Country-level emotion aggregation tests
├── collective_analyzer/test_app.py  # Collective vs personal classification tests
├── cross_country_detector/test_app.py # Cross-country mention detection tests
├── cache_service/test_app.py        # Redis cache tests
├── search_service/test_app.py       # Search functionality tests
├── stats_service/test_app.py        # Statistics endpoint tests
├── scheduler/test_app.py            # Smart scheduling tests
├── url_extractor/test_app.py        # URL content extraction tests
└── db_cleanup/test_app.py           # Database cleanup tests
```

## Running Tests

### Run Tests for a Single Service

Navigate to a service directory and run:

```bash
cd backend/services/api_gateway
pytest test_app.py -v
```

### Run All Tests

From the project root:

```bash
# Run all tests
pytest backend/services/*/test_app.py -v

# Run with coverage report
pytest backend/services/*/test_app.py --cov=backend/services --cov-report=html

# Run specific test class
pytest backend/services/api_gateway/test_app.py::TestHealth -v

# Run specific test
pytest backend/services/api_gateway/test_app.py::TestHealth::test_health_endpoint -v
```

### Run Tests for a Specific Service Category

```bash
# Core ML/Analysis services
pytest backend/services/ml_analyzer/test_app.py \
       backend/services/collective_analyzer/test_app.py \
       backend/services/cross_country_detector/test_app.py -v

# Data services
pytest backend/services/post_fetcher/test_app.py \
       backend/services/url_extractor/test_app.py \
       backend/services/country_aggregation/test_app.py -v

# Infrastructure services
pytest backend/services/cache_service/test_app.py \
       backend/services/search_service/test_app.py \
       backend/services/stats_service/test_app.py -v
```

## Test Coverage

Generate a coverage report:

```bash
# HTML coverage report
pytest backend/services/*/test_app.py --cov=backend/services --cov-report=html
open htmlcov/index.html

# Terminal coverage report
pytest backend/services/*/test_app.py --cov=backend/services --cov-report=term

# XML coverage report (for CI/CD)
pytest backend/services/*/test_app.py --cov=backend/services --cov-report=xml
```

## Test Structure

Each test file follows this structure:

```python
# Fixtures for test setup
@pytest.fixture
def client():
    """Create Flask test client"""
    
@pytest.fixture
def mock_db():
    """Mock database connection"""

# Test classes organized by functionality
class TestHealth:
    """Test health endpoint"""
    
class TestCoreLogic:
    """Test main business logic"""
    
class TestAPIEndpoints:
    """Test API endpoints"""
    
class TestDatabase:
    """Test database operations"""
    
class TestRabbitMQ:
    """Test message queue integration"""
```

## Testing Dependencies

All services include these testing dependencies in `requirements.txt`:

```
pytest==7.4.3          # Test framework
pytest-cov==4.1.0      # Coverage plugin
pytest-mock==3.12.0    # Mocking utilities
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r backend/services/api_gateway/requirements.txt
          # ... install for other services
      - name: Run tests
        run: pytest backend/services/*/test_app.py --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Writing New Tests

When adding new functionality, follow these guidelines:

1. **Test Naming**: Use descriptive names starting with `test_`
2. **Test Organization**: Group related tests in classes
3. **Mocking**: Mock external dependencies (database, RabbitMQ, external APIs)
4. **Assertions**: Use specific assertions with helpful messages
5. **Edge Cases**: Test both happy paths and error conditions

Example:

```python
def test_new_feature_success(self, client, mock_db):
    """Test new feature with valid input"""
    # Arrange
    mock_db.return_value = expected_data
    
    # Act
    response = client.post('/api/endpoint', json={'data': 'test'})
    
    # Assert
    assert response.status_code == 200
    assert 'expected_key' in response.json
```

## Test Data

Tests use mocked data and do not require:
- Running Docker containers
- PostgreSQL database
- RabbitMQ server
- Redis cache
- External APIs (Reddit, etc.)

This allows tests to run quickly and independently.

## Troubleshooting

### Import Errors

If you see import errors, ensure you're running pytest from the correct directory:

```bash
cd backend/services/api_gateway
PYTHONPATH=. pytest test_app.py
```

### Mock Issues

If mocks aren't working, verify the patch path matches the import in the tested file:

```python
# If app.py has: import psycopg2
# Use: @patch('app.psycopg2')

# If app.py has: from psycopg2 import connect
# Use: @patch('app.connect')
```

### Environment Variables

Tests set required environment variables automatically. If needed, you can override:

```bash
DATABASE_URL=test RABBITMQ_URL=test pytest test_app.py
```

## Contributing

When adding new services:

1. Create `test_app.py` in the service directory
2. Add pytest dependencies to `requirements.txt`
3. Write tests covering all endpoints and core logic
4. Ensure tests pass: `pytest test_app.py -v`
5. Check coverage: `pytest test_app.py --cov=app`

Aim for >80% code coverage on all services.

## Summary

- ✅ **12 services** with comprehensive unit tests
- ✅ **200+ test cases** covering all major functionality
- ✅ **Mocked dependencies** for fast, isolated testing
- ✅ **CI/CD ready** for automated testing
- ✅ **Coverage reports** to track test quality

Run `pytest backend/services/*/test_app.py -v` to verify all tests pass!
