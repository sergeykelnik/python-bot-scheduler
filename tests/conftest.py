"""Shared pytest configuration and fixtures"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add the project root to the Python path (parent of tests folder)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_telegram_api():
    """Mock Telegram API responses"""
    with patch('bot.requests') as mock_requests:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_requests.post.return_value = mock_response
        mock_requests.get.return_value = mock_response
        yield mock_requests


@pytest.fixture
def mock_database():
    """Create a mock database"""
    db = Mock()
    db.get_schedules = Mock(return_value=[])
    db.save_schedule = Mock()
    db.delete_schedule = Mock()
    db.update_schedule_pause_status = Mock()
    return db


@pytest.fixture
def mock_scheduler():
    """Create a mock scheduler"""
    scheduler = Mock()
    scheduler.scheduled_jobs = {}
    scheduler.start = Mock()
    scheduler.shutdown = Mock()
    scheduler.pause_job = Mock(return_value=True)
    scheduler.resume_job = Mock(return_value=True)
    scheduler.delete_job = Mock(return_value=True)
    scheduler.create_daily_schedule = Mock(return_value={'description': 'Test schedule'})
    scheduler.create_interval_schedule = Mock(return_value={'description': 'Test schedule'})
    scheduler.create_cron_schedule = Mock(return_value={'description': 'Test schedule'})
    return scheduler


@pytest.fixture
def mock_handlers():
    """Create a mock message handlers"""
    handlers = Mock()
    handlers.handle_start = Mock()
    handlers.handle_help = Mock()
    handlers.handle_schedule = Mock()
    handlers.handle_list = Mock()
    handlers.handle_manage = Mock()
    handlers.handle_getchatid = Mock()
    handlers.handle_callback_query = Mock()
    handlers.handle_text_message = Mock()
    return handlers


@pytest.fixture(autouse=True)
def clear_user_states():
    """Clear user states before each test"""
    from handlers import user_states
    user_states.clear()
    yield
    user_states.clear()
