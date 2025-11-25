# Quick Start: Running Tests

## One-Line Setup

```bash
# Install dependencies if not already done
pip install -r requirements.txt

# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Open coverage report in browser
start htmlcov/index.html
```

## Common Test Commands

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests |
| `pytest -v` | Run all tests (verbose) |
| `pytest -q` | Run all tests (quiet) |
| `pytest test_bot.py` | Run only bot tests |
| `pytest test_bot.py::test_send_message_success` | Run one specific test |
| `pytest -k "send_message"` | Run tests matching pattern |
| `pytest --cov=.` | Run tests with coverage |
| `pytest --cov=. --cov-report=html` | Generate HTML coverage report |
| `pytest -x` | Stop on first failure |
| `pytest --lf` | Run last failed tests |
| `pytest --tb=short` | Short traceback format |
| `pytest --tb=no` | No traceback on failures |

## Test Coverage Report

After running `pytest --cov=. --cov-report=html`:
- Open `htmlcov/index.html` to see detailed coverage
- Coverage report shows:
  - Line-by-line code coverage
  - Which lines are not covered
  - Percentage coverage per file

## Files in This Test Suite

- **test_bot.py** - 21 tests for TelegramBot class
- **test_database.py** - 12 tests for Database class  
- **test_handlers.py** - 34 tests for MessageHandlers class
- **test_scheduler.py** - 26 tests for SchedulerManager class
- **test_schedule_manager.py** - 22 tests for ScheduleManager class
- **conftest.py** - Shared fixtures and configuration
- **TESTS.md** - Detailed test documentation
- **TEST_SUMMARY.md** - Summary of test coverage

## What's Being Tested

✅ Bot initialization and setup  
✅ Message sending and formatting  
✅ Command processing (/start, /help, /schedule, etc.)  
✅ Callback query handling (inline buttons)  
✅ Database operations (save, delete, update)  
✅ Schedule creation and parsing  
✅ Schedule management (pause, resume, delete)  
✅ User state management  
✅ Permission checks  
✅ Error handling  
✅ AI-based schedule parsing  

## Example Test Output

```
$ pytest -v

test_bot.py::test_bot_initialization PASSED              [  4%]
test_bot.py::test_send_message_success PASSED            [ 14%]
test_database.py::test_save_schedule PASSED              [ 20%]
test_handlers.py::test_parse_daily_schedule_valid PASSED [ 40%]
test_scheduler.py::test_create_daily_schedule PASSED     [ 75%]

============================= 115 passed in 11.03s ==============================
```

## Debugging Tips

### Run a single test with full output:
```bash
pytest test_bot.py::test_send_message_success -vv
```

### Show print statements in tests:
```bash
pytest -s
```

### Get detailed failure information:
```bash
pytest --tb=long
```

### Run tests in parallel (faster):
```bash
pytest -n auto
```

### Watch files and rerun tests on changes:
```bash
pytest-watch
```

## Integration with IDEs

### VS Code
- Install Python extension
- Tests automatically discovered in left sidebar
- Run/debug individual tests from the sidebar

### PyCharm
- Tests automatically discovered
- Green checkmark shows passing tests
- Red X shows failing tests
- Right-click test → Run/Debug

## Continuous Integration

These tests are designed for CI/CD:
- All dependencies in requirements.txt
- Tests run without external services
- Exit code 0 on success, non-zero on failure
- Coverage reports can be generated
- Works on Windows, Linux, macOS

## Performance

- **Total time**: ~11 seconds for 115 tests
- **No external dependencies**: All APIs mocked
- **Parallel capable**: Tests are independent
- **Memory efficient**: Temporary database files cleaned up

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Run tests: `pytest`
3. ✅ View coverage: `pytest --cov=. --cov-report=html && start htmlcov/index.html`
4. ✅ Add new tests as you add features

## Need Help?

- Run `pytest --help` for all options
- Check TESTS.md for detailed test documentation
- Check TEST_SUMMARY.md for coverage breakdown
- Each test file has docstrings explaining what it tests

Happy testing! 🧪
