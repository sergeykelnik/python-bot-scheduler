"""Tests for the main TelegramBot class"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from bot import TelegramBot


@pytest.fixture
def mock_bot():
    """Create a TelegramBot instance with mocked dependencies"""
    with patch('bot.Database'), \
         patch('bot.SchedulerManager'), \
         patch('bot.MessageHandlers'), \
         patch('bot.requests.post') as mock_post:
        
        # Mock the successful response for set_bot_commands
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        bot = TelegramBot('test_token_123')
        return bot


def test_bot_initialization(mock_bot):
    """Test that TelegramBot initializes correctly"""
    assert mock_bot.token == 'test_token_123'
    assert mock_bot.base_url == 'https://api.telegram.org/bottest_token_123'
    assert mock_bot.last_update_id == 0
    assert mock_bot.db is not None
    assert mock_bot.scheduler is not None
    assert mock_bot.handlers is not None


def test_set_bot_commands(mock_bot):
    """Test that bot commands are set during initialization"""
    with patch('bot.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        mock_bot.set_bot_commands()
        
        # Verify that post was called with correct URL
        assert mock_post.called
        call_args = mock_post.call_args
        assert '/setMyCommands' in call_args[0][0]


def test_send_message_success(mock_bot):
    """Test successful message sending"""
    with patch('bot.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True, 'result': {'message_id': 1}}
        mock_post.return_value = mock_response
        
        result = mock_bot.send_message(123, "Hello World")
        
        assert result['ok'] is True
        assert mock_post.called


def test_send_message_with_reply_markup(mock_bot):
    """Test message sending with inline keyboard"""
    with patch('bot.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        markup = {'inline_keyboard': [[{'text': 'Button', 'callback_data': 'btn_1'}]]}
        result = mock_bot.send_message(123, "Test", reply_markup=markup)
        
        assert result['ok'] is True
        # Verify markup was included in the call
        call_kwargs = mock_post.call_args[1]
        assert 'json' in call_kwargs
        assert call_kwargs['json']['reply_markup'] == markup


def test_send_message_error_handling(mock_bot):
    """Test error handling in message sending"""
    with patch('bot.requests.post') as mock_post:
        mock_post.side_effect = Exception("Network error")
        
        result = mock_bot.send_message(123, "Hello")
        
        assert result is None


def test_send_scheduled_message(mock_bot):
    """Test sending a scheduled message"""
    with patch.object(mock_bot, 'send_message') as mock_send:
        mock_bot.send_scheduled_message(123, "Scheduled message")
        
        mock_send.assert_called_once_with(123, "Scheduled message")


def test_answer_callback_query(mock_bot):
    """Test answering callback queries"""
    with patch('bot.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        result = mock_bot.answer_callback_query('callback_123', 'Got it!', show_alert=True)
        
        assert result['ok'] is True
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs['json']['callback_query_id'] == 'callback_123'
        assert call_kwargs['json']['text'] == 'Got it!'


def test_edit_message_text(mock_bot):
    """Test editing message text"""
    with patch('bot.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        result = mock_bot.edit_message_text(123, 456, "New text")
        
        assert result['ok'] is True
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs['json']['chat_id'] == 123
        assert call_kwargs['json']['message_id'] == 456
        assert call_kwargs['json']['text'] == "New text"


def test_edit_message_reply_markup(mock_bot):
    """Test editing message reply markup"""
    with patch('bot.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        markup = {'inline_keyboard': [[{'text': 'New Button', 'callback_data': 'new_btn'}]]}
        result = mock_bot.edit_message_reply_markup(123, 456, markup)
        
        assert result['ok'] is True
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs['json']['reply_markup'] == markup


def test_get_updates_success(mock_bot):
    """Test successful update retrieval"""
    with patch('bot.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            'ok': True,
            'result': [
                {'update_id': 1, 'message': {'chat': {'id': 123}, 'from': {'id': 456}, 'text': 'Hello'}}
            ]
        }
        mock_get.return_value = mock_response
        
        result = mock_bot.get_updates(offset=1)
        
        assert result['ok'] is True
        assert len(result['result']) == 1


def test_get_updates_error_handling(mock_bot):
    """Test error handling in get_updates"""
    with patch('bot.requests.get') as mock_get:
        mock_get.side_effect = Exception("Network error")
        
        result = mock_bot.get_updates()
        
        assert result is None


def test_process_update_text_message(mock_bot):
    """Test processing a text message update"""
    update = {
        'update_id': 1,
        'message': {
            'chat': {'id': 123},
            'from': {'id': 456},
            'text': 'Hello bot'
        }
    }
    
    mock_bot.handlers.handle_text_message = Mock()
    mock_bot.process_update(update)
    
    mock_bot.handlers.handle_text_message.assert_called_once_with(123, 456, 'Hello bot')


def test_process_update_start_command(mock_bot):
    """Test processing /start command"""
    update = {
        'update_id': 1,
        'message': {
            'chat': {'id': 123},
            'from': {'id': 456},
            'text': '/start'
        }
    }
    
    mock_bot.handlers.handle_start = Mock()
    mock_bot.process_update(update)
    
    mock_bot.handlers.handle_start.assert_called_once_with(123, 456)


def test_process_update_help_command(mock_bot):
    """Test processing /help command"""
    update = {
        'update_id': 1,
        'message': {
            'chat': {'id': 123},
            'from': {'id': 456},
            'text': '/help'
        }
    }
    
    mock_bot.handlers.handle_help = Mock()
    mock_bot.process_update(update)
    
    mock_bot.handlers.handle_help.assert_called_once_with(123, 456)


def test_process_update_schedule_command(mock_bot):
    """Test processing /schedule command"""
    update = {
        'update_id': 1,
        'message': {
            'chat': {'id': 123},
            'from': {'id': 456},
            'text': '/schedule'
        }
    }
    
    mock_bot.handlers.handle_schedule = Mock()
    mock_bot.process_update(update)
    
    mock_bot.handlers.handle_schedule.assert_called_once_with(123, 456)


def test_process_update_list_command(mock_bot):
    """Test processing /list command"""
    update = {
        'update_id': 1,
        'message': {
            'chat': {'id': 123},
            'from': {'id': 456},
            'text': '/list'
        }
    }
    
    mock_bot.handlers.handle_list = Mock()
    mock_bot.process_update(update)
    
    mock_bot.handlers.handle_list.assert_called_once_with(123, 456)


def test_process_update_manage_command(mock_bot):
    """Test processing /manage command"""
    update = {
        'update_id': 1,
        'message': {
            'chat': {'id': 123},
            'from': {'id': 456},
            'text': '/manage'
        }
    }
    
    mock_bot.handlers.handle_manage = Mock()
    mock_bot.process_update(update)
    
    mock_bot.handlers.handle_manage.assert_called_once_with(123, 456)


def test_process_update_getchatid_command(mock_bot):
    """Test processing /getchatid command"""
    update = {
        'update_id': 1,
        'message': {
            'chat': {'id': 123},
            'from': {'id': 456},
            'text': '/getchatid'
        }
    }
    
    mock_bot.handlers.handle_getchatid = Mock()
    mock_bot.process_update(update)
    
    mock_bot.handlers.handle_getchatid.assert_called_once_with(123, 456)


def test_process_update_callback_query(mock_bot):
    """Test processing callback query from inline buttons"""
    update = {
        'update_id': 1,
        'callback_query': {
            'id': 'callback_123',
            'from': {'id': 456},
            'data': 'cmd:schedule',
            'message': {
                'chat': {'id': 123},
                'message_id': 789
            }
        }
    }
    
    mock_bot.handlers.handle_callback_query = Mock()
    mock_bot.process_update(update)
    
    # Verify the callback query handler was called
    assert mock_bot.handlers.handle_callback_query.called


def test_process_update_ignores_non_message(mock_bot):
    """Test that updates without messages are ignored"""
    update = {'update_id': 1}
    
    mock_bot.handlers.handle_text_message = Mock()
    mock_bot.process_update(update)
    
    mock_bot.handlers.handle_text_message.assert_not_called()


def test_process_update_ignores_no_text(mock_bot):
    """Test that messages without text are ignored"""
    update = {
        'update_id': 1,
        'message': {
            'chat': {'id': 123},
            'from': {'id': 456},
            'photo': [{'file_id': 'photo_123'}]
        }
    }
    
    mock_bot.handlers.handle_text_message = Mock()
    mock_bot.process_update(update)
    
    mock_bot.handlers.handle_text_message.assert_not_called()
