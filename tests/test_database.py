"""Tests for the Database class"""

import pytest
import sqlite3
import json
from unittest.mock import Mock, patch, MagicMock
from database import Database


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing"""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    yield db
    # Cleanup happens automatically when tmp_path is cleaned up


@pytest.fixture
def sample_schedule():
    """Sample schedule data for testing"""
    return {
        'job_id': 'job_123_456',
        'user_id': 123,
        'chat_id': '456',
        'message': 'Test message',
        'schedule_type': 'daily',
        'schedule_data': {'hour': 9, 'minute': 0, 'description': 'Daily at 09:00'},
        'is_paused': False
    }


def test_database_initialization(temp_db):
    """Test that database is initialized correctly"""
    assert temp_db.db_path is not None
    
    # Check that table exists
    with sqlite3.connect(temp_db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schedules'")
        assert cursor.fetchone() is not None


def test_save_schedule(temp_db, sample_schedule):
    """Test saving a schedule to the database"""
    temp_db.save_schedule(
        job_id=sample_schedule['job_id'],
        user_id=sample_schedule['user_id'],
        chat_id=sample_schedule['chat_id'],
        message=sample_schedule['message'],
        schedule_type=sample_schedule['schedule_type'],
        schedule_data=sample_schedule['schedule_data'],
        is_paused=sample_schedule['is_paused']
    )
    
    # Retrieve and verify
    schedules = temp_db.get_schedules()
    assert len(schedules) == 1
    assert schedules[0]['job_id'] == sample_schedule['job_id']
    assert schedules[0]['user_id'] == sample_schedule['user_id']


def test_save_schedule_multiple(temp_db):
    """Test saving multiple schedules"""
    for i in range(3):
        temp_db.save_schedule(
            job_id=f'job_123_{i}',
            user_id=123,
            chat_id='456',
            message=f'Message {i}',
            schedule_type='daily',
            schedule_data={'hour': 9, 'minute': 0},
            is_paused=False
        )
    
    schedules = temp_db.get_schedules()
    assert len(schedules) == 3


def test_get_schedules_by_user(temp_db):
    """Test retrieving schedules for a specific user"""
    # Save schedules for different users
    temp_db.save_schedule('job_1', 123, '456', 'Message 1', 'daily', {'hour': 9, 'minute': 0}, False)
    temp_db.save_schedule('job_2', 789, '012', 'Message 2', 'daily', {'hour': 10, 'minute': 0}, False)
    temp_db.save_schedule('job_3', 123, '456', 'Message 3', 'interval', {'interval': 30, 'unit': 'minutes'}, False)
    
    # Get schedules for user 123
    user_schedules = temp_db.get_schedules(user_id=123)
    assert len(user_schedules) == 2
    assert all(s['user_id'] == 123 for s in user_schedules)


def test_delete_schedule(temp_db, sample_schedule):
    """Test deleting a schedule"""
    temp_db.save_schedule(
        job_id=sample_schedule['job_id'],
        user_id=sample_schedule['user_id'],
        chat_id=sample_schedule['chat_id'],
        message=sample_schedule['message'],
        schedule_type=sample_schedule['schedule_type'],
        schedule_data=sample_schedule['schedule_data']
    )
    
    # Verify it exists
    schedules = temp_db.get_schedules()
    assert len(schedules) == 1
    
    # Delete it
    temp_db.delete_schedule(sample_schedule['job_id'])
    
    # Verify it's gone
    schedules = temp_db.get_schedules()
    assert len(schedules) == 0


def test_delete_nonexistent_schedule(temp_db):
    """Test deleting a schedule that doesn't exist (should not raise error)"""
    # This should not raise an exception
    temp_db.delete_schedule('nonexistent_job')
    
    schedules = temp_db.get_schedules()
    assert len(schedules) == 0


def test_update_schedule_pause_status(temp_db, sample_schedule):
    """Test updating pause status of a schedule"""
    temp_db.save_schedule(
        job_id=sample_schedule['job_id'],
        user_id=sample_schedule['user_id'],
        chat_id=sample_schedule['chat_id'],
        message=sample_schedule['message'],
        schedule_type=sample_schedule['schedule_type'],
        schedule_data=sample_schedule['schedule_data'],
        is_paused=False
    )
    
    # Verify initial state
    schedules = temp_db.get_schedules()
    assert schedules[0]['is_paused'] is False
    
    # Update to paused
    temp_db.update_schedule_pause_status(sample_schedule['job_id'], True)
    
    # Verify updated state
    schedules = temp_db.get_schedules()
    assert schedules[0]['is_paused'] is True
    
    # Update back to active
    temp_db.update_schedule_pause_status(sample_schedule['job_id'], False)
    
    # Verify updated state
    schedules = temp_db.get_schedules()
    assert schedules[0]['is_paused'] is False


def test_save_schedule_with_complex_data(temp_db):
    """Test saving schedule with complex schedule_data"""
    complex_data = {
        'expression': '0 9 * * MON',
        'description': 'Every Monday at 09:00',
        'extra_field': 'extra_value'
    }
    
    temp_db.save_schedule(
        job_id='job_complex',
        user_id=123,
        chat_id='456',
        message='Complex schedule',
        schedule_type='cron',
        schedule_data=complex_data
    )
    
    schedules = temp_db.get_schedules()
    assert schedules[0]['schedule_data'] == complex_data


def test_replace_existing_schedule(temp_db):
    """Test that saving with same job_id replaces the schedule"""
    temp_db.save_schedule('job_1', 123, '456', 'Original message', 'daily', {'hour': 9, 'minute': 0}, False)
    
    # Save with same job_id but different data
    temp_db.save_schedule('job_1', 123, '789', 'Updated message', 'daily', {'hour': 10, 'minute': 0}, False)
    
    schedules = temp_db.get_schedules()
    assert len(schedules) == 1
    assert schedules[0]['message'] == 'Updated message'
    assert schedules[0]['chat_id'] == '789'


def test_schedule_data_json_serialization(temp_db):
    """Test that complex schedule_data is properly serialized/deserialized"""
    original_data = {
        'nested': {'key': 'value', 'list': [1, 2, 3]},
        'string': 'test',
        'number': 42
    }
    
    temp_db.save_schedule(
        'job_1', 123, '456', 'Message', 'custom', original_data
    )
    
    schedules = temp_db.get_schedules()
    assert schedules[0]['schedule_data'] == original_data


def test_empty_get_schedules(temp_db):
    """Test getting schedules when database is empty"""
    schedules = temp_db.get_schedules()
    assert schedules == []


def test_empty_get_schedules_for_user(temp_db):
    """Test getting schedules for a user with no schedules"""
    temp_db.save_schedule('job_1', 123, '456', 'Message', 'daily', {'hour': 9, 'minute': 0})
    
    user_schedules = temp_db.get_schedules(user_id=999)
    assert user_schedules == []


def test_add_recent_chat_id(temp_db):
    """Test adding recent chat IDs"""
    temp_db.add_recent_chat_id(123, 456)
    
    recent = temp_db.get_recent_chat_ids(123)
    assert 456 in recent
    assert len(recent) == 1


def test_add_multiple_recent_chat_ids(temp_db):
    """Test adding multiple recent chat IDs"""
    temp_db.add_recent_chat_id(123, 456)
    temp_db.add_recent_chat_id(123, 789)
    temp_db.add_recent_chat_id(123, 101112)
    
    recent = temp_db.get_recent_chat_ids(123)
    assert len(recent) == 3
    assert 456 in recent
    assert 789 in recent
    assert 101112 in recent


def test_recent_chat_ids_order(temp_db):
    """Test that most recent chat ID is first"""
    temp_db.add_recent_chat_id(123, 456)
    temp_db.add_recent_chat_id(123, 789)
    
    recent = temp_db.get_recent_chat_ids(123)
    assert recent[0] == 789  # Most recent should be first
    assert recent[1] == 456


def test_recent_chat_ids_max_limit(temp_db):
    """Test that only max 5 recent chat IDs are stored"""
    for i in range(10):
        temp_db.add_recent_chat_id(123, 100 + i)
    
    recent = temp_db.get_recent_chat_ids(123)
    assert len(recent) == 5  # Should only keep 5 most recent


def test_duplicate_recent_chat_id_moves_to_front(temp_db):
    """Test that adding duplicate chat ID moves it to front"""
    temp_db.add_recent_chat_id(123, 456)
    temp_db.add_recent_chat_id(123, 789)
    temp_db.add_recent_chat_id(123, 456)  # Add again
    
    recent = temp_db.get_recent_chat_ids(123)
    assert recent[0] == 456  # Should be moved to front
    assert recent[1] == 789
    assert len(recent) == 2


def test_get_recent_chat_ids_empty(temp_db):
    """Test getting recent chat IDs for user with none"""
    recent = temp_db.get_recent_chat_ids(123)
    assert recent == []


def test_get_recent_chat_ids_nonexistent_user(temp_db):
    """Test getting recent chat IDs for nonexistent user"""
    recent = temp_db.get_recent_chat_ids(999)
    assert recent == []
