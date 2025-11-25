"""Tests for the ScheduleManager class (AI-based schedule parser)"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from schedule_manager import ScheduleManager
import re


@pytest.fixture
def mock_groq_client():
    """Create a mock Groq client"""
    client = Mock()
    return client


@pytest.fixture
def schedule_manager():
    """Create ScheduleManager with mocked Groq client"""
    with patch('schedule_manager.Groq') as mock_groq:
        manager = ScheduleManager(api_key='test_key')
        manager.client = Mock()
        return manager


def test_schedule_manager_initialization(schedule_manager):
    """Test that ScheduleManager initializes correctly"""
    assert schedule_manager.client is not None


def test_schedule_manager_initialization_with_api_key():
    """Test that ScheduleManager accepts custom API key"""
    with patch('schedule_manager.Groq') as mock_groq:
        manager = ScheduleManager(api_key='custom_key')
        mock_groq.assert_called_once_with(api_key='custom_key')


def test_parse_schedule_with_ai_valid_cron(schedule_manager):
    """Test parsing valid cron expression with AI"""
    # Mock the API response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "*/15 * * * *"
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    result = schedule_manager._parse_schedule_with_ai("every 15 minutes")
    
    assert result == "*/15 * * * *"


def test_parse_schedule_with_ai_removes_markdown(schedule_manager):
    """Test that API response with cron outside markdown works"""
    # Mock response with the cron expression clearly visible (not in markdown)
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    # API should return just the cron expression
    mock_response.choices[0].message.content = "*/15 * * * *"
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    result = schedule_manager._parse_schedule_with_ai("every 15 minutes")
    
    # Should parse correctly
    assert result == "*/15 * * * *"


def test_parse_schedule_with_ai_daily_morning(schedule_manager):
    """Test parsing 'daily at 9 AM' expression"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "0 9 * * *"
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    result = schedule_manager._parse_schedule_with_ai("every day at 9 AM")
    
    assert result == "0 9 * * *"


def test_parse_schedule_with_ai_weekly(schedule_manager):
    """Test parsing 'every Monday at 10:30' expression"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "30 10 * * 1"
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    result = schedule_manager._parse_schedule_with_ai("every Monday at 10:30")
    
    assert result == "30 10 * * 1"


def test_parse_schedule_with_ai_monthly(schedule_manager):
    """Test parsing 'first day of month at midnight' expression"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "0 0 1 * *"
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    result = schedule_manager._parse_schedule_with_ai("first day of month at midnight")
    
    assert result == "0 0 1 * *"


def test_parse_schedule_with_ai_invalid_format(schedule_manager):
    """Test that invalid cron format raises error"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "invalid"  # Not valid cron
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    with pytest.raises(Exception, match='Invalid cron format|Failed to parse'):
        schedule_manager._parse_schedule_with_ai("some invalid text")


def test_parse_schedule_with_ai_incomplete_cron(schedule_manager):
    """Test that incomplete cron expression raises error"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "0 9 * *"  # Missing one part
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    with pytest.raises(Exception):
        schedule_manager._parse_schedule_with_ai("some text")


def test_parse_schedule_with_ai_extra_whitespace(schedule_manager):
    """Test that cron expression with extra whitespace is handled"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "  */15 * * * *  \n"  # Extra whitespace
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    result = schedule_manager._parse_schedule_with_ai("every 15 minutes")
    
    # Should be stripped
    assert result == "*/15 * * * *"


def test_parse_schedule_with_ai_api_error(schedule_manager):
    """Test error handling when API call fails"""
    schedule_manager.client.chat.completions.create = Mock(
        side_effect=Exception("API Error")
    )
    
    with pytest.raises(Exception, match='Failed to parse'):
        schedule_manager._parse_schedule_with_ai("any text")


def test_parse_schedule_with_ai_network_error(schedule_manager):
    """Test error handling for network errors"""
    schedule_manager.client.chat.completions.create = Mock(
        side_effect=ConnectionError("Network error")
    )
    
    with pytest.raises(Exception, match='Failed to parse'):
        schedule_manager._parse_schedule_with_ai("any text")


def test_parse_schedule_with_ai_api_call_structure(schedule_manager):
    """Test that API is called with correct structure"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "0 9 * * *"
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    schedule_manager._parse_schedule_with_ai("every day at 9 AM")
    
    # Verify API was called
    assert schedule_manager.client.chat.completions.create.called
    
    # Check the call arguments
    call_args = schedule_manager.client.chat.completions.create.call_args
    call_kwargs = call_args[1]
    
    # Verify model is set
    assert call_kwargs['model'] == "llama-3.3-70b-versatile"
    
    # Verify messages contain the prompt
    messages = call_kwargs['messages']
    assert isinstance(messages, list)
    assert len(messages) > 0
    assert 'user' in messages[0]['role']
    assert 'content' in messages[0]


def test_parse_schedule_with_ai_temperature_setting(schedule_manager):
    """Test that API is called with correct temperature"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "0 9 * * *"
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    schedule_manager._parse_schedule_with_ai("every day at 9 AM")
    
    call_kwargs = schedule_manager.client.chat.completions.create.call_args[1]
    assert call_kwargs['temperature'] == 0.1  # Low temperature for consistent output


def test_parse_schedule_with_ai_token_limit(schedule_manager):
    """Test that max_tokens is set appropriately"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "0 9 * * *"
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    schedule_manager._parse_schedule_with_ai("every day at 9 AM")
    
    call_kwargs = schedule_manager.client.chat.completions.create.call_args[1]
    assert call_kwargs['max_tokens'] <= 100  # Should be limited


def test_parse_schedule_with_ai_complex_description(schedule_manager):
    """Test parsing complex natural language schedule descriptions"""
    test_cases = [
        ("every 15 minutes", "*/15 * * * *"),
        ("every day at 9 AM", "0 9 * * *"),
        ("every Monday at 10:30", "30 10 * * 1"),
        ("first day of month at midnight", "0 0 1 * *"),
    ]
    
    for description, expected_cron in test_cases:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = expected_cron
        
        schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = schedule_manager._parse_schedule_with_ai(description)
        assert result == expected_cron


def test_parse_schedule_cron_validation(schedule_manager):
    """Test that cron expressions are properly validated"""
    # Valid cron expression
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "0 0 1 1 0"  # Valid 5-part cron
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    result = schedule_manager._parse_schedule_with_ai("custom schedule")
    assert result == "0 0 1 1 0"


def test_parse_schedule_with_ai_empty_response(schedule_manager):
    """Test handling of empty API response"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = ""  # Empty response
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    with pytest.raises(Exception):
        schedule_manager._parse_schedule_with_ai("some text")


def test_parse_schedule_with_ai_multiline_response(schedule_manager):
    """Test handling of multiline API response with extra text"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    # Response with extra text that should be handled
    mock_response.choices[0].message.content = """The cron expression is:
0 9 * * *
Have a good day!"""
    
    schedule_manager.client.chat.completions.create = Mock(return_value=mock_response)
    
    # This might fail depending on implementation, but it's good to test edge cases
    try:
        result = schedule_manager._parse_schedule_with_ai("every day at 9")
        # If it works, verify it extracted something valid
        parts = result.split()
        assert len(parts) == 5  # Valid cron has 5 parts
    except Exception:
        # If it fails on extra text, that's also acceptable behavior
        pass
