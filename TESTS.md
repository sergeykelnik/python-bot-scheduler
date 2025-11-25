"""
Tests Overview and Running Instructions

This directory contains comprehensive unit tests for the Telegram Bot Scheduler project.
All tests use mocks to isolate components and avoid external dependencies.

## Test Files

### test_bot.py
Tests for the main TelegramBot class:
- Bot initialization and setup
- Message sending (with and without markup)
- Command processing (/start, /help, /schedule, /list, /manage, /getchatid)
- Callback query handling from inline buttons
- Update processing (messages, callback queries, various edge cases)
- Bot menu commands setup

Key fixtures:
- `mock_bot`: TelegramBot instance with all dependencies mocked

### test_database.py
Tests for the Database class:
- Database initialization and table creation
- Saving schedules with various data types
- Retrieving schedules (all or for specific user)
- Deleting schedules
- Updating pause/resume status
- Edge cases (empty database, non-existent schedules, etc.)

Key features:
- Uses temporary SQLite database for each test
- Tests JSON serialization/deserialization
- Validates data persistence

### test_handlers.py
Tests for the MessageHandlers class:
- Command handlers (/start, /help, /schedule, /list, /manage, /getchatid)
- Text message processing with state machine
- Callback query handling (pause, resume, delete, confirm)
- Schedule parsing (daily, interval, cron)
- Permission checks for schedule management
- Keyboard markup generation

Parsing tests cover:
- Daily schedules: "daily HH:MM"
- Interval schedules: "every X hours/minutes/seconds"
- Error handling and validation

### test_scheduler.py
Tests for the SchedulerManager class:
- Creating different schedule types (daily, interval, cron)
- Pausing and resuming jobs
- Deleting jobs
- Loading schedules from database
- Job trigger creation (CronTrigger, IntervalTrigger)
- Error handling for invalid schedules

### test_schedule_manager.py
Tests for the ScheduleManager (AI schedule parser) class:
- Parsing natural language to cron expressions
- API response handling and markdown cleanup
- Cron validation (5-part format)
- Error handling for API failures
- Various schedule descriptions (daily, weekly, monthly, intervals)

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with verbose output:
```bash
pytest -v
```

### Run specific test file:
```bash
pytest test_bot.py
```

### Run specific test function:
```bash
pytest test_bot.py::test_bot_initialization
```

### Run tests with coverage report:
```bash
pytest --cov=. --cov-report=html
```

This generates HTML coverage report in htmlcov/index.html

### Run tests matching a pattern:
```bash
pytest -k "test_send_message"
```

### Run with markers:
```bash
pytest -m "not slow"
```

## Test Structure

All tests follow this pattern:
1. **Setup**: Create mocks and fixtures
2. **Act**: Call the function being tested
3. **Assert**: Verify expected behavior

## Mocking Strategy

The tests use Python's `unittest.mock` library to:
- Mock external API calls (Telegram API via requests)
- Mock database operations (SQLite)
- Mock scheduler operations (APScheduler)
- Mock Groq API for AI-based schedule parsing

Benefits:
- Tests run without external dependencies
- Tests run fast (no network calls)
- Tests are isolated and repeatable
- Tests don't modify real database or send real messages

## Test Coverage

The test suite covers:
- ✅ Normal/happy path scenarios
- ✅ Edge cases and boundary conditions
- ✅ Error handling and exceptions
- ✅ Permission and authorization checks
- ✅ State management and transitions
- ✅ Data persistence and retrieval

## Writing New Tests

When adding new functionality, follow this pattern:

```python
@pytest.fixture
def mock_bot():
    # Create mocks
    return bot

def test_new_feature(mock_bot):
    # Arrange
    mock_bot.some_method = Mock(return_value=expected_value)
    
    # Act
    result = mock_bot.new_feature()
    
    # Assert
    assert result == expected_value
    mock_bot.some_method.assert_called_once()
```

## Dependencies

Testing dependencies are in requirements.txt:
- `pytest`: Test framework
- `pytest-cov`: Coverage reporting
- `pytest-mock`: Mocking utilities

## CI/CD Integration

These tests are designed to be run in CI/CD pipelines:
- Tests exit with code 0 on success
- Tests exit with non-zero code on failure
- Coverage reports can be generated for analysis

## Troubleshooting

### Import errors
Make sure the project root is in PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Mock not working
Verify the patch path matches the module import path where the object is used, not where it's defined.

### Test isolation issues
The `conftest.py` provides fixtures that automatically clean up state between tests.
Use the `clear_user_states` fixture for tests involving user_states.

## Future Improvements

Potential areas for test expansion:
- Integration tests for multi-step user flows
- Performance/load tests for large schedule numbers
- Async tests if async functionality is added
- Property-based tests using hypothesis library
"""

# This file serves as documentation only, not executable code
