"""
Smoke tests for the aiogram-based bot.
Covers:
1. Database initialization and async CRUD.
2. Scheduler service cron validation and job management.
3. Bot + Dispatcher construction and wiring.
"""

import pytest
import pytest_asyncio

from src.bot.database import Database
from src.bot.scheduler_service import SchedulerService


# --- Database Smoke Tests ---

@pytest_asyncio.fixture
async def temp_db(tmp_path):
    """Create a temporary async database for testing."""
    db_path = tmp_path / "smoke_test.db"
    db = Database(str(db_path))
    await db.init()
    return db


@pytest.mark.asyncio
async def test_database_smoke(temp_db):
    """Verify database can init, save, retrieve, update, and delete a schedule."""
    db = temp_db

    # Save
    await db.save_schedule(
        job_id="smoke_job_1",
        user_id=101,
        chat_id="202",
        message="Smoke Test",
        schedule_data={"expression": "0 9 * * *", "description": "desc"},
        is_paused=False,
    )

    # Retrieve
    schedules = await db.get_schedules(user_id=101)
    assert len(schedules) == 1
    assert schedules[0]["job_id"] == "smoke_job_1"
    assert schedules[0]["message"] == "Smoke Test"

    # Update (Pause)
    await db.update_schedule_pause_status("smoke_job_1", True)
    updated = (await db.get_schedules(user_id=101))[0]
    assert updated["is_paused"] is True

    # Delete
    await db.delete_schedule("smoke_job_1")
    assert len(await db.get_schedules(user_id=101)) == 0


@pytest.mark.asyncio
async def test_user_language_smoke(temp_db):
    """Verify user language preference CRUD."""
    db = temp_db

    # Default
    assert await db.get_user_language(999) == "ru"

    # Set
    await db.set_user_language(999, "en")
    assert await db.get_user_language(999) == "en"

    # Update (same method — INSERT OR REPLACE)
    await db.set_user_language(999, "ru")
    assert await db.get_user_language(999) == "ru"


# --- Scheduler Smoke Tests ---

@pytest.fixture
def scheduler_service(mocker):
    """Create SchedulerService with mocked AsyncIOScheduler."""
    mocker.patch("src.bot.scheduler_service.AsyncIOScheduler")
    service = SchedulerService(mocker.AsyncMock())
    service.scheduler = mocker.Mock()
    service.scheduler.add_job = mocker.Mock()
    service.scheduler.get_job = mocker.Mock(return_value=True)
    service.scheduler.remove_job = mocker.Mock()
    return service


def test_scheduler_add_job(scheduler_service):
    """Verify scheduler can add a job with valid cron."""
    res = scheduler_service.add_job(
        job_id="smoke_job_1",
        chat_id="202",
        message="Smoke Test",
        cron_expression="0 12 * * *",
    )
    assert res["expression"] == "0 12 * * *"
    assert "description" in res


def test_scheduler_pause_delete(scheduler_service):
    """Verify scheduler can pause and delete jobs."""
    assert scheduler_service.pause_job("smoke_job_1") is True
    assert scheduler_service.delete_job("smoke_job_1") is True


def test_scheduler_invalid_cron(scheduler_service):
    """Verify scheduler rejects invalid cron."""
    with pytest.raises(ValueError, match="Invalid cron"):
        scheduler_service.add_job("bad", "202", "msg", "not a cron")


# --- Bot Smoke Tests ---

def test_bot_build_smoke(mocker):
    """Verify bot and dispatcher build without errors and wire all components."""
    mocker.patch("src.bot.bot.Bot")
    mocker.patch("src.bot.bot.SchedulerService")
    mocker.patch("src.bot.bot.AIService")

    from src.bot.bot import build_bot_and_dispatcher
    bot, dp = build_bot_and_dispatcher()

    assert dp["db"] is not None
    assert dp["translator"] is not None
    assert dp["scheduler"] is not None
    assert dp["ai_service"] is not None
    assert len(dp.sub_routers) == 2
