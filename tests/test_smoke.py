"""
Critical smoke tests for the application.
Covers:
1. Database initialization and basic CRUD.
2. Scheduler service startup and job management.
3. Bot initialization and component wiring.
"""

import pytest
from unittest.mock import Mock, patch
from src.core.database import Database
from src.services.scheduler_service import SchedulerService
from src.bot.telegram_bot import TelegramBot

# --- Database Smoke Tests ---

@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing"""
    db_path = tmp_path / "smoke_test.db"
    db = Database(str(db_path))
    yield db

def test_database_smoke(temp_db):
    """Verify database can init, save, and retrieve a schedule."""
    # 1. Save
    temp_db.save_schedule(
        job_id='smoke_job_1',
        user_id=101,
        chat_id='202',
        message='Smoke Test',
        schedule_data={'expression': '0 9 * * *', 'description': 'desc'},
        is_paused=False
    )
    
    # 2. Retrieve
    schedules = temp_db.get_schedules(user_id=101)
    assert len(schedules) == 1
    assert schedules[0]['job_id'] == 'smoke_job_1'
    assert schedules[0]['message'] == 'Smoke Test'
    
    # 3. Update (Pause)
    temp_db.update_schedule_pause_status('smoke_job_1', True)
    updated = temp_db.get_schedules(user_id=101)[0]
    assert updated['is_paused'] is True
    
    # 4. Delete
    temp_db.delete_schedule('smoke_job_1')
    assert len(temp_db.get_schedules(user_id=101)) == 0


# --- Scheduler Smoke Tests ---

@pytest.fixture
def scheduler_service():
    """Create SchedulerService with mocked internal APScheduler"""
    with patch('src.services.scheduler_service.BackgroundScheduler'):
        service = SchedulerService(Mock())
        # Mock the internal scheduler object to avoid real background threads
        service.scheduler = Mock()
        service.scheduler.add_job = Mock()
        service.scheduler.get_job = Mock(return_value=True) # Pretend job exists
        service.scheduler.remove_job = Mock()
        yield service

def test_scheduler_smoke(scheduler_service):
    """Verify scheduler can add, pause, and delete jobs."""
    # 1. Add Job
    # We must provide a valid cron expression for the service validation logic
    res = scheduler_service.add_job(
        job_id='smoke_job_1',
        chat_id='202',
        message='Smoke Test',
        cron_expression='0 12 * * *'
    )
    assert res['expression'] == '0 12 * * *'
    
    # 2. Pause
    # Mock get_job to return something so pause logic proceeds
    scheduler_service.scheduler.get_job.return_value = True 
    assert scheduler_service.pause_job('smoke_job_1') is True
    
    # 3. Delete
    assert scheduler_service.delete_job('smoke_job_1') is True


# --- Bot Smoke Tests ---

@pytest.fixture
def mock_bot():
    """Create a TelegramBot instance with mocked dependencies for smoke testing."""
    with patch('src.bot.telegram_bot.Database'), \
         patch('src.bot.telegram_bot.SchedulerService'), \
         patch('src.bot.telegram_bot.AIService'), \
         patch('src.bot.telegram_bot.TranslationService'), \
         patch('src.bot.telegram_bot.MessageHandlers'), \
         patch('src.bot.telegram_bot.requests.post') as mock_post:
        
        # Mock successful API response for setMyCommands
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        bot = TelegramBot('test_token_smoke')
        return bot

def test_bot_startup_smoke(mock_bot):
    """Verify bot initializes components correctly."""
    assert mock_bot.token == 'test_token_smoke'
    assert mock_bot.db is not None
    assert mock_bot.scheduler is not None
    assert mock_bot.ai_service is not None
    assert mock_bot.translator is not None
    assert mock_bot.handlers is not None
