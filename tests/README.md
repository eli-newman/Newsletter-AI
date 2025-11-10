# Tests

Test suite for RSS Feed Summarizer.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rss_feed_summarizer --cov=distribution --cov-report=html

# Run specific test file
pytest tests/test_fetcher.py

# Run specific test
pytest tests/test_fetcher.py::TestRSSFetcher::test_init_with_defaults

# Run with verbose output
pytest -v
```

## Test Structure

- `conftest.py` - Shared fixtures and pytest configuration
- `test_fetcher.py` - Tests for RSS feed fetching
- `test_pipeline.py` - Tests for main pipeline orchestration
- `test_distribution.py` - Tests for email distribution
- `test_sheets_db.py` - Tests for Google Sheets integration
- `test_cache_utils.py` - Tests for cache utilities

## Writing Tests

When adding new tests:

1. Follow pytest conventions (test files start with `test_`, test functions start with `test_`)
2. Use fixtures from `conftest.py` when possible
3. Mock external dependencies (API calls, file I/O, etc.)
4. Keep tests focused and independent
5. Use descriptive test names

## Coverage

Aim for >80% code coverage. Run coverage reports with:

```bash
pytest --cov=rss_feed_summarizer --cov=distribution --cov-report=term-missing
```

