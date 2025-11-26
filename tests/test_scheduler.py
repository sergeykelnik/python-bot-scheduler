"""Tests for the SchedulerManager class"""

import pytest
from unittest.mock import Mock, patch, MagicMock, ANY
from scheduler import SchedulerManager


@pytest.fixture
def mock_bot():
    """Create a mock bot instance"""
    bot = Mock()
    bot.send_scheduled_message = Mock()
    bot.db = Mock()
    return bot


@pytest.fixture
def scheduler_manager(mock_bot):
    """Create SchedulerManager instance with mock bot"""
    with patch('scheduler.BackgroundScheduler'):
        manager = SchedulerManager(mock_bot)
        manager.scheduler = Mock()  # Mock the scheduler object itself
        return manager


def test_scheduler_manager_initialization(scheduler_manager, mock_bot):
    """Test that SchedulerManager initializes correctly"""
    assert scheduler_manager.bot == mock_bot
    assert scheduler_manager.scheduled_jobs == {}
    assert scheduler_manager.scheduler is not None


def test_create_daily_schedule(scheduler_manager, mock_bot):
    """Test creating a daily schedule"""
    with patch.object(scheduler_manager, '_add_job_to_scheduler') as mock_add:
        result = scheduler_manager.create_daily_schedule(
            'job_1', '123', 'Test message', 9, 30
        )
    
    assert result['hour'] == 9
    assert result['minute'] == 30
    assert 'description' in result
    assert '09:30' in result['description']


def test_create_interval_schedule_hours(scheduler_manager):
    """Test creating an interval schedule with hours"""
    with patch.object(scheduler_manager, '_add_job_to_scheduler'):
        result = scheduler_manager.create_interval_schedule(
            'job_1', '123', 'Message', 2, 'hours'
        )
    
    assert result['interval'] == 2
    assert result['unit'] == 'hours'
    assert 'описание' in result['description'].lower() or 'description' in str(result)


def test_create_interval_schedule_minutes(scheduler_manager):
    """Test creating an interval schedule with minutes"""
    with patch.object(scheduler_manager, '_add_job_to_scheduler'):
        result = scheduler_manager.create_interval_schedule(
            'job_1', '123', 'Message', 30, 'minutes'
        )
    
    assert result['interval'] == 30
    assert result['unit'] == 'minutes'


def test_create_interval_schedule_seconds(scheduler_manager):
    """Test creating an interval schedule with seconds"""
    with patch.object(scheduler_manager, '_add_job_to_scheduler'):
        result = scheduler_manager.create_interval_schedule(
            'job_1', '123', 'Message', 10, 'seconds'
        )
    
    assert result['interval'] == 10
    assert result['unit'] == 'seconds'


def test_create_cron_schedule(scheduler_manager):
    """Test creating a cron schedule"""
    with patch.object(scheduler_manager, '_add_job_to_scheduler'):
        result = scheduler_manager.create_cron_schedule(
            'job_1', '123', 'Message', '0 9 * * MON'
        )
    
    assert result['expression'] == '0 9 * * MON'
    assert 'description' in result


def test_pause_job(scheduler_manager):
    """Test pausing a job"""
    scheduler_manager.scheduler.get_job = Mock(return_value=Mock())
    scheduler_manager.scheduler.remove_job = Mock()
    
    result = scheduler_manager.pause_job('job_1')
    
    assert result is True
    scheduler_manager.scheduler.remove_job.assert_called_once_with('job_1')


def test_pause_job_not_found(scheduler_manager):
    """Test pausing a job that doesn't exist"""
    scheduler_manager.scheduler.get_job = Mock(return_value=None)
    
    result = scheduler_manager.pause_job('nonexistent_job')
    
    assert result is True  # Still returns True


def test_pause_job_error(scheduler_manager):
    """Test error handling when pausing a job"""
    scheduler_manager.scheduler.get_job = Mock(side_effect=Exception("Error"))
    
    result = scheduler_manager.pause_job('job_1')
    
    assert result is False


def test_resume_job(scheduler_manager):
    """Test resuming a job"""
    with patch.object(scheduler_manager, '_add_job_to_scheduler'):
        result = scheduler_manager.resume_job(
            'job_1', {'hour': 9, 'minute': 0}, '123', 'Message'
        )
    
    assert result is True


def test_resume_job_error(scheduler_manager):
    """Test error handling when resuming a job"""
    with patch.object(scheduler_manager, '_add_job_to_scheduler', side_effect=Exception("Error")):
        result = scheduler_manager.resume_job(
            'job_1', {'hour': 9, 'minute': 0}, '123', 'Message'
        )
    
    assert result is False


def test_delete_job(scheduler_manager):
    """Test deleting a job"""
    scheduler_manager.scheduler.get_job = Mock(return_value=Mock())
    scheduler_manager.scheduler.remove_job = Mock()
    
    result = scheduler_manager.delete_job('job_1')
    
    assert result is True
    scheduler_manager.scheduler.remove_job.assert_called_once_with('job_1')


def test_delete_job_not_found(scheduler_manager):
    """Test deleting a job that doesn't exist"""
    scheduler_manager.scheduler.get_job = Mock(return_value=None)
    
    result = scheduler_manager.delete_job('nonexistent_job')
    
    assert result is True  # Still returns True


def test_delete_job_error(scheduler_manager):
    """Test error handling when deleting a job"""
    scheduler_manager.scheduler.get_job = Mock(side_effect=Exception("Error"))
    
    result = scheduler_manager.delete_job('job_1')
    
    assert result is False


def test_start_scheduler(scheduler_manager):
    """Test starting the scheduler"""
    scheduler_manager.start()
    
    scheduler_manager.scheduler.start.assert_called_once()


def test_shutdown_scheduler(scheduler_manager):
    """Test shutting down the scheduler"""
    scheduler_manager.shutdown()
    
    scheduler_manager.scheduler.shutdown.assert_called_once()


def test_load_schedules_from_db_empty(scheduler_manager, mock_bot):
    """Test loading schedules when database is empty"""
    mock_bot.db.get_schedules = Mock(return_value=[])
    
    scheduler_manager.load_schedules_from_db()
    
    assert scheduler_manager.scheduled_jobs == {}


def test_load_schedules_from_db_single(scheduler_manager, mock_bot):
    """Test loading a single schedule from database"""
    schedule = {
        'job_id': 'job_1',
        'user_id': 123,
        'chat_id': '456',
        'message': 'Test message',
        'schedule_data': {'hour': 9, 'minute': 0, 'description': 'Daily at 09:00'},
        'is_paused': False
    }
    mock_bot.db.get_schedules = Mock(return_value=[schedule])
    
    with patch.object(scheduler_manager, '_add_job_to_scheduler'):
        scheduler_manager.load_schedules_from_db()
    
    assert 'job_1' in scheduler_manager.scheduled_jobs
    assert scheduler_manager.scheduled_jobs['job_1']['user_id'] == 123


def test_load_schedules_from_db_paused_not_added(scheduler_manager, mock_bot):
    """Test that paused schedules are not added to scheduler but stored in memory"""
    schedule = {
        'job_id': 'job_1',
        'user_id': 123,
        'chat_id': '456',
        'message': 'Test message',
        'schedule_data': {'hour': 9, 'minute': 0, 'description': 'Daily at 09:00'},
        'is_paused': True
    }
    mock_bot.db.get_schedules = Mock(return_value=[schedule])
    
    with patch.object(scheduler_manager, '_add_job_to_scheduler') as mock_add:
        scheduler_manager.load_schedules_from_db()
    
    # Should not add to scheduler
    mock_add.assert_not_called()
    # But should be in memory
    assert 'job_1' in scheduler_manager.scheduled_jobs
    assert scheduler_manager.scheduled_jobs['job_1']['is_paused'] is True


def test_load_schedules_from_db_multiple(scheduler_manager, mock_bot):
    """Test loading multiple schedules from database"""
    schedules = [
        {
            'job_id': f'job_{i}',
            'user_id': 123 + i,
            'chat_id': f'{456 + i}',
            'message': f'Message {i}',
            'schedule_data': {'hour': 9, 'minute': 0, 'description': f'Daily at 09:00'},
            'is_paused': False
        }
        for i in range(3)
    ]
    mock_bot.db.get_schedules = Mock(return_value=schedules)
    
    with patch.object(scheduler_manager, '_add_job_to_scheduler'):
        scheduler_manager.load_schedules_from_db()
    
    assert len(scheduler_manager.scheduled_jobs) == 3
    for i in range(3):
        assert f'job_{i}' in scheduler_manager.scheduled_jobs


def test_load_schedules_from_db_with_error(scheduler_manager, mock_bot):
    """Test that load continues even if one schedule has error"""
    schedules = [
        {
            'job_id': 'job_1',
            'user_id': 123,
            'chat_id': '456',
            'message': 'Message 1',
            'schedule_data': {'hour': 9, 'minute': 0},
            'is_paused': False
        },
        {
            'job_id': 'job_2',
            'user_id': 124,
            'chat_id': '457',
            'message': 'Message 2',
            'schedule_data': {'hour': 10, 'minute': 0},
            'is_paused': False
        }
    ]
    mock_bot.db.get_schedules = Mock(return_value=schedules)
    
    with patch.object(scheduler_manager, '_add_job_to_scheduler') as mock_add:
        # First call raises error, second succeeds
        mock_add.side_effect = [Exception("Error"), None]
        scheduler_manager.load_schedules_from_db()
    
    # Should have loaded job_2 even though job_1 failed
    assert 'job_2' in scheduler_manager.scheduled_jobs


def test_add_job_daily_trigger(scheduler_manager):
    """Test adding a job with daily trigger"""
    with patch('scheduler.CronTrigger') as mock_cron:
        scheduler_manager._add_job_to_scheduler(
            'job_1', 'daily',
            {'hour': 9, 'minute': 30},
            '123', 'Message'
        )
    
    # Verify CronTrigger was created with correct parameters
    mock_cron.assert_called_once()
    call_kwargs = mock_cron.call_args[1]
    assert call_kwargs['hour'] == 9
    assert call_kwargs['minute'] == 30
    
    # Verify job was added to scheduler
    scheduler_manager.scheduler.add_job.assert_called_once()


def test_add_job_interval_trigger_hours(scheduler_manager):
    """Test adding a job with interval trigger (hours)"""
    with patch('scheduler.IntervalTrigger') as mock_interval:
        scheduler_manager._add_job_to_scheduler(
            'job_1', 'interval',
            {'interval': 2, 'unit': 'hours'},
            '123', 'Message'
        )
    
    # Verify IntervalTrigger was created
    mock_interval.assert_called_once()
    call_kwargs = mock_interval.call_args[1]
    assert call_kwargs['hours'] == 2


def test_add_job_interval_trigger_minutes(scheduler_manager):
    """Test adding a job with interval trigger (minutes)"""
    with patch('scheduler.IntervalTrigger') as mock_interval:
        scheduler_manager._add_job_to_scheduler(
            'job_1', 'interval',
            {'interval': 30, 'unit': 'minutes'},
            '123', 'Message'
        )
    
    # Verify IntervalTrigger was created
    mock_interval.assert_called_once()
    call_kwargs = mock_interval.call_args[1]
    assert call_kwargs['minutes'] == 30


def test_add_job_interval_trigger_seconds(scheduler_manager):
    """Test adding a job with interval trigger (seconds)"""
    with patch('scheduler.IntervalTrigger') as mock_interval:
        scheduler_manager._add_job_to_scheduler(
            'job_1', 'interval',
            {'interval': 10, 'unit': 'seconds'},
            '123', 'Message'
        )
    
    # Verify IntervalTrigger was created
    mock_interval.assert_called_once()
    call_kwargs = mock_interval.call_args[1]
    assert call_kwargs['seconds'] == 10


def test_add_job_cron_trigger(scheduler_manager):
    """Test adding a job with cron trigger"""
    with patch('scheduler.CronTrigger') as mock_cron:
        scheduler_manager._add_job_to_scheduler(
            'job_1', 'cron',
            {'expression': '0 9 * * MON'},
            '123', 'Message'
        )
    
    # Verify CronTrigger.from_crontab was called
    mock_cron.from_crontab.assert_called_once_with('0 9 * * MON', timezone=ANY)


def test_add_job_invalid_schedule_type(scheduler_manager):
    """Test that invalid schedule type raises error"""
    with pytest.raises(ValueError, match='Unknown schedule type'):
        scheduler_manager._add_job_to_scheduler(
            'job_1', 'invalid_type',
            {},
            '123', 'Message'
        )


def test_add_job_invalid_interval_unit(scheduler_manager):
    """Test that invalid interval unit raises error"""
    with pytest.raises(ValueError, match='Unknown interval unit'):
        scheduler_manager._add_job_to_scheduler(
            'job_1', 'interval',
            {'interval': 5, 'unit': 'days'},
            '123', 'Message'
        )


def test_add_job_calls_scheduler_add_job(scheduler_manager):
    """Test that add_job_to_scheduler calls scheduler.add_job"""
    with patch('scheduler.CronTrigger'):
        scheduler_manager._add_job_to_scheduler(
            'job_1', 'daily',
            {'hour': 9, 'minute': 0},
            '123', 'Message'
        )
    
    # Verify scheduler.add_job was called with correct parameters
    scheduler_manager.scheduler.add_job.assert_called_once()
    call_args = scheduler_manager.scheduler.add_job.call_args
    assert call_args[1]['id'] == 'job_1'
    assert call_args[1]['args'] == ['123', 'Message']
