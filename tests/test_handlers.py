"""Tests for the MessageHandlers class"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from handlers import MessageHandlers, user_states


@pytest.fixture
def mock_bot():
    """Create a mock bot instance"""
    bot = Mock()
    bot.send_message = Mock()
    bot.answer_callback_query = Mock()
    bot.edit_message_text = Mock()
    bot.edit_message_reply_markup = Mock()
    bot.db = Mock()
    bot.scheduler = Mock()
    bot.scheduler.scheduled_jobs = {}
    return bot


@pytest.fixture
def handlers(mock_bot):
    """Create MessageHandlers instance with mock bot"""
    return MessageHandlers(mock_bot)


def test_handlers_initialization(handlers, mock_bot):
    """Test that MessageHandlers initializes correctly"""
    assert handlers.bot == mock_bot
    assert handlers.schedule_manager is not None


def test_handle_start(handlers, mock_bot):
    """Test /start command handler"""
    handlers.handle_start(123, 456)
    
    # Verify send_message was called
    assert mock_bot.send_message.called
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == 123  # chat_id
    assert 'Выберите действие' in call_args[0][1]
    # Verify reply_markup was sent
    assert call_args[1]['reply_markup'] is not None


def test_handle_help(handlers, mock_bot):
    """Test /help command handler"""
    handlers.handle_help(123, 456)
    
    # Verify send_message was called with help text
    assert mock_bot.send_message.called
    call_args = mock_bot.send_message.call_args
    assert 'Помощь' in call_args[0][1] or 'daily' in call_args[0][1]


def test_handle_getchatid(handlers, mock_bot):
    """Test /getchatid command handler"""
    handlers.handle_getchatid(123, 456)
    
    # Verify send_message was called with chat ID
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert '123' in call_args[0][1]  # chat_id should be in the message


def test_handle_schedule(handlers, mock_bot):
    """Test /schedule command handler"""
    user_id = 456
    handlers.handle_schedule(123, user_id)
    
    # Verify user state was set
    assert user_id in user_states
    assert user_states[user_id]['step'] == 'chat_id'
    
    # Verify message was sent
    mock_bot.send_message.assert_called_once()


def test_handle_list_no_jobs(handlers, mock_bot):
    """Test /list command with no schedules"""
    mock_bot.scheduler.scheduled_jobs = {}
    
    handlers.handle_list(123, 456)
    
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert 'нет' in call_args[0][1].lower()


def test_handle_list_with_jobs(handlers, mock_bot):
    """Test /list command with active schedules"""
    mock_bot.scheduler.scheduled_jobs = {
        'job_1': {
            'user_id': 456,
            'chat_id': '123',
            'message': 'Test message',
            'schedule': 'daily 09:00',
            'is_paused': False
        },
        'job_2': {
            'user_id': 456,
            'chat_id': '123',
            'message': 'Another message',
            'schedule': 'daily 14:00',
            'is_paused': True
        }
    }
    
    handlers.handle_list(123, 456)
    
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert 'job_1' in call_args[0][1]
    assert 'job_2' in call_args[0][1]


def test_handle_list_filters_by_user(handlers, mock_bot):
    """Test that /list only shows current user's schedules"""
    mock_bot.scheduler.scheduled_jobs = {
        'job_1': {
            'user_id': 456,
            'chat_id': '123',
            'message': 'User 456 message',
            'schedule': 'daily 09:00',
            'is_paused': False
        },
        'job_2': {
            'user_id': 789,
            'chat_id': '123',
            'message': 'User 789 message',
            'schedule': 'daily 14:00',
            'is_paused': False
        }
    }
    
    handlers.handle_list(123, 456)
    
    call_args = mock_bot.send_message.call_args
    message = call_args[0][1]
    assert 'job_1' in message
    assert 'job_2' not in message


def test_handle_manage_no_jobs(handlers, mock_bot):
    """Test /manage command with no schedules"""
    mock_bot.scheduler.scheduled_jobs = {}
    
    handlers.handle_manage(123, 456)
    
    call_args = mock_bot.send_message.call_args
    assert 'нет' in call_args[0][1].lower()


def test_handle_manage_with_jobs(handlers, mock_bot):
    """Test /manage command with schedules"""
    mock_bot.scheduler.scheduled_jobs = {
        'job_1': {
            'user_id': 456,
            'chat_id': '123',
            'message': 'Test message',
            'schedule': 'daily 09:00',
            'is_paused': False
        }
    }
    
    handlers.handle_manage(123, 456)
    
    # Should send one message per job
    assert mock_bot.send_message.call_count == 1
    call_args = mock_bot.send_message.call_args
    # Should have inline_keyboard
    assert 'reply_markup' in call_args[1]
    assert 'inline_keyboard' in call_args[1]['reply_markup']


def test_parse_daily_schedule_valid(handlers):
    """Test parsing valid daily schedule"""
    hour, minute = handlers._parse_daily_schedule('daily 09:30')
    assert hour == 9
    assert minute == 30


def test_parse_daily_schedule_different_times(handlers):
    """Test parsing different times"""
    test_cases = [
        ('daily 00:00', 0, 0),
        ('daily 23:59', 23, 59),
        ('daily 12:45', 12, 45),
    ]
    
    for schedule_text, expected_hour, expected_minute in test_cases:
        hour, minute = handlers._parse_daily_schedule(schedule_text)
        assert hour == expected_hour
        assert minute == expected_minute


def test_parse_daily_schedule_invalid_format(handlers):
    """Test parsing invalid daily schedule"""
    with pytest.raises(ValueError, match='Формат'):
        handlers._parse_daily_schedule('daily')


def test_parse_daily_schedule_invalid_time(handlers):
    """Test parsing invalid time values"""
    with pytest.raises(ValueError, match='Неверное время'):
        handlers._parse_daily_schedule('daily 25:00')


def test_parse_interval_schedule_valid(handlers):
    """Test parsing valid interval schedule"""
    interval, unit = handlers._parse_interval_schedule('every 30 minutes')
    assert interval == 30
    assert unit == 'minutes'


def test_parse_interval_schedule_hours(handlers):
    """Test parsing hour interval"""
    interval, unit = handlers._parse_interval_schedule('every 2 hours')
    assert interval == 2
    assert unit == 'hours'


def test_parse_interval_schedule_seconds(handlers):
    """Test parsing second interval"""
    interval, unit = handlers._parse_interval_schedule('every 10 seconds')
    assert interval == 10
    assert unit == 'seconds'


def test_parse_interval_schedule_invalid_format(handlers):
    """Test parsing invalid interval schedule"""
    with pytest.raises(ValueError, match='Формат'):
        handlers._parse_interval_schedule('every 30')


def test_parse_interval_schedule_invalid_interval(handlers):
    """Test parsing interval with non-numeric value"""
    with pytest.raises(ValueError, match='числом'):
        handlers._parse_interval_schedule('every abc minutes')


def test_parse_interval_schedule_invalid_unit(handlers):
    """Test parsing interval with invalid unit"""
    with pytest.raises(ValueError, match='Единица'):
        handlers._parse_interval_schedule('every 30 days')


def test_handle_text_message_chat_id_step(handlers, mock_bot):
    """Test text message handling in chat_id step"""
    user_id = 456
    user_states[user_id] = {'step': 'chat_id'}
    
    handlers.handle_text_message(123, user_id, 'me')
    
    # Should transition to message step
    assert user_states[user_id]['step'] == 'message'
    assert user_states[user_id]['chat_id'] == 123
    mock_bot.send_message.assert_called_once()


def test_handle_text_message_message_step(handlers, mock_bot):
    """Test text message handling in message step"""
    user_id = 456
    user_states[user_id] = {'step': 'message', 'chat_id': 123}
    
    handlers.handle_text_message(123, user_id, 'Test message')
    
    # Should transition to schedule step
    assert user_states[user_id]['step'] == 'schedule'
    assert user_states[user_id]['message'] == 'Test message'
    mock_bot.send_message.assert_called_once()


def test_handle_callback_query_command_schedule(handlers, mock_bot):
    """Test callback query for schedule command"""
    handlers.handle_callback_query({}, 'cq_1', 456, 123, 789, 'schedule:me')
    
    # Should set user state
    assert 456 in user_states
    assert user_states[456]['step'] == 'message'
    assert user_states[456]['chat_id'] == 123


def test_handle_callback_query_command_list(handlers, mock_bot):
    """Test callback query for list command"""
    mock_bot.scheduler.scheduled_jobs = {}
    
    handlers.handle_callback_query({}, 'cq_1', 456, 123, 789, 'cmd:list')
    
    # Should call handle_list
    mock_bot.send_message.assert_called()
    mock_bot.answer_callback_query.assert_called_once()


def test_handle_callback_query_command_help(handlers, mock_bot):
    """Test callback query for help command"""
    handlers.handle_callback_query({}, 'cq_1', 456, 123, 789, 'cmd:help')
    
    # Should call handle_help
    mock_bot.send_message.assert_called()


def test_handle_callback_query_invalid_data(handlers, mock_bot):
    """Test callback query with invalid data"""
    handlers.handle_callback_query({}, 'cq_1', 456, 123, 789, None)
    
    # Should still acknowledge the query
    mock_bot.answer_callback_query.assert_called_once()


def test_handle_callback_query_pause_job(handlers, mock_bot):
    """Test pausing a job via callback"""
    job_id = 'job_1'
    user_id = 456
    
    mock_bot.scheduler.scheduled_jobs = {
        job_id: {
            'user_id': user_id,
            'chat_id': '123',
            'message': 'Test',
            'schedule': 'daily 09:00',
            'is_paused': False
        }
    }
    mock_bot.scheduler.pause_job = Mock(return_value=True)
    mock_bot.db.update_schedule_pause_status = Mock()
    
    handlers.handle_callback_query({}, 'cq_1', user_id, 123, 789, f'manage:pause:{job_id}')
    
    # Should pause the job
    mock_bot.scheduler.pause_job.assert_called_once_with(job_id)
    mock_bot.db.update_schedule_pause_status.assert_called_once()


def test_handle_callback_query_delete_job_confirmation(handlers, mock_bot):
    """Test initiating job deletion with confirmation"""
    job_id = 'job_1'
    user_id = 456
    
    mock_bot.scheduler.scheduled_jobs = {
        job_id: {
            'user_id': user_id,
            'chat_id': '123',
            'message': 'Test',
            'schedule': 'daily 09:00',
            'is_paused': False
        }
    }
    
    handlers.handle_callback_query({}, 'cq_1', user_id, 123, 789, f'manage:delete:{job_id}')
    
    # Should edit message with confirmation buttons
    mock_bot.edit_message_text.assert_called_once()
    call_args = mock_bot.edit_message_text.call_args
    assert 'Подтвердите удаление' in call_args[0][2]


def test_handle_callback_query_confirm_delete(handlers, mock_bot):
    """Test confirming job deletion"""
    job_id = 'job_1'
    user_id = 456
    
    mock_bot.scheduler.scheduled_jobs = {
        job_id: {
            'user_id': user_id,
            'chat_id': '123',
            'message': 'Test',
            'schedule': 'daily 09:00',
            'is_paused': False
        }
    }
    mock_bot.scheduler.delete_job = Mock(return_value=True)
    mock_bot.db.delete_schedule = Mock()
    
    handlers.handle_callback_query({}, 'cq_1', user_id, 123, 789, f'confirm_delete:{job_id}')
    
    # Should delete the job
    mock_bot.scheduler.delete_job.assert_called_once_with(job_id)
    mock_bot.db.delete_schedule.assert_called_once_with(job_id)


def test_handle_callback_query_permission_denied(handlers, mock_bot):
    """Test that users can't manage other users' jobs"""
    job_id = 'job_1'
    owner_id = 789
    user_id = 456  # Different user
    
    mock_bot.scheduler.scheduled_jobs = {
        job_id: {
            'user_id': owner_id,
            'chat_id': '123',
            'message': 'Test',
            'schedule': 'daily 09:00',
            'is_paused': False
        }
    }
    
    handlers.handle_callback_query({}, 'cq_1', user_id, 123, 789, f'manage:pause:{job_id}')
    
    # Should show permission denied
    mock_bot.answer_callback_query.assert_called()
    call_args = mock_bot.answer_callback_query.call_args
    assert 'нет прав' in call_args[1]['text'].lower() or 'права' in call_args[1]['text'].lower()


def test_build_job_text(handlers):
    """Test building job text for display"""
    job_info = {
        'chat_id': '123',
        'message': 'Test message',
        'schedule': 'daily 09:00',
        'is_paused': False
    }
    
    text = handlers._build_job_text('job_1', job_info)
    
    assert 'job_1' in text
    assert 'АКТИВНО' in text or 'PAUSED' not in text
    assert '123' in text
    assert 'Test message' in text


def test_build_job_text_paused(handlers):
    """Test building text for paused job"""
    job_info = {
        'chat_id': '123',
        'message': 'Test message',
        'schedule': 'daily 09:00',
        'is_paused': True
    }
    
    text = handlers._build_job_text('job_1', job_info)
    
    assert 'ПРИОСТАНОВЛЕНО' in text or 'PAUSED' in text


def test_build_job_markup_active(handlers):
    """Test building keyboard markup for active job"""
    job_info = {'is_paused': False}
    
    markup = handlers._build_job_markup('job_1', job_info)
    
    assert 'inline_keyboard' in markup
    buttons = markup['inline_keyboard'][0]
    button_texts = [btn['text'] for btn in buttons]
    assert any('Приостановить' in text or 'Pause' in text for text in button_texts)


def test_build_job_markup_paused(handlers):
    """Test building keyboard markup for paused job"""
    job_info = {'is_paused': True}
    
    markup = handlers._build_job_markup('job_1', job_info)
    
    assert 'inline_keyboard' in markup
    buttons = markup['inline_keyboard'][0]
    button_texts = [btn['text'] for btn in buttons]
    assert any('Возобновить' in text or 'Resume' in text for text in button_texts)
