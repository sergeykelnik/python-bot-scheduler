"""
FSM states for the schedule creation wizard and editing.
"""

from aiogram.fsm.state import State, StatesGroup


class ScheduleWizard(StatesGroup):
    """Three-step schedule creation flow."""

    waiting_chat_id = State()
    waiting_message = State()
    waiting_schedule = State()


class EditWizard(StatesGroup):
    """Two-step schedule editing flow."""

    waiting_message = State()
    waiting_schedule = State()


