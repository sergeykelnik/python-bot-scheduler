"""
Scheduler service built on APScheduler AsyncIOScheduler.
"""

import logging
from typing import Any, Callable, Coroutine, Dict, Set, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.bot.config import WARSAW_TZ

logger = logging.getLogger(__name__)


class SchedulerService:
    """Manages async cron-based jobs via APScheduler."""

    VALID_DAY_NAMES: Set[str] = {
        "SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT",
        "0", "1", "2", "3", "4", "5", "6", "7",
    }
    VALID_MONTH_NAMES: Set[str] = {
        "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
    }

    def __init__(
        self,
        callback_func: Callable[..., Coroutine[Any, Any, None]],
    ):
        """
        Args:
            callback_func: async callable(chat_id, message) invoked on trigger.
        """
        self.scheduler = AsyncIOScheduler(timezone=WARSAW_TZ)
        self.callback_func = callback_func

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("AsyncIOScheduler started.")

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("AsyncIOScheduler shut down.")

    # ------------------------------------------------------------------
    # Cron validation
    # ------------------------------------------------------------------

    def _validate_cron_field(self, field: str, field_type: str) -> bool:
        if not field:
            return False
        if field == "*":
            return True

        if "/" in field:
            parts = field.split("/")
            if len(parts) != 2:
                return False
            base, step = parts
            try:
                int(step)
            except ValueError:
                return False
            return base == "*" or self._validate_cron_field(base, field_type)

        if "-" in field:
            parts = field.split("-")
            if len(parts) != 2:
                return False
            for p in parts:
                if p and not p[0].isdigit() and p.upper() not in (self.VALID_DAY_NAMES | self.VALID_MONTH_NAMES):
                    try:
                        int(p)
                    except ValueError:
                        return False
            return True

        if "," in field:
            return all(self._validate_cron_field(p, field_type) for p in field.split(","))

        try:
            int(field)
            return True
        except ValueError:
            return field.upper() in (self.VALID_DAY_NAMES | self.VALID_MONTH_NAMES)

    def validate_cron_expression(self, expression: str) -> Tuple[bool, str]:
        expression = expression.strip()
        parts = expression.split()
        if len(parts) != 5:
            return False, f"Cron must have 5 fields (minute hour day month weekday), got {len(parts)}"

        field_names = ("minute", "hour", "day", "month", "weekday")
        for field, name in zip(parts, field_names):
            if not self._validate_cron_field(field, name):
                return False, f"Invalid {name} field: {field}"

        return True, ""

    # ------------------------------------------------------------------
    # Day-of-week conversion (Unix → APScheduler)
    # ------------------------------------------------------------------

    def _convert_cron_to_apscheduler_format(self, expression: str) -> str:
        parts = expression.split()
        if len(parts) != 5:
            return expression

        minute, hour, day, month, weekday = parts

        if weekday in ("*", "?"):
            return expression

        if any(n in weekday.upper() for n in ("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT")):
            return expression

        def _convert_dow(dow: str) -> str:
            if dow in ("*", "?"):
                return dow
            if "-" in dow and "," not in dow:
                a, b = dow.split("-", 1)
                try:
                    s, e = int(a), int(b)
                    cs, ce = (s - 1) % 7, (e - 1) % 7
                    return f"{cs}-{ce}" if cs <= ce else f"{cs},0-{ce}"
                except (ValueError, IndexError):
                    return dow
            if "," in dow:
                items = dow.split(",")
                converted = []
                for item in items:
                    if "-" in item:
                        converted.append(_convert_dow(item))
                    else:
                        try:
                            converted.append(str((int(item) - 1) % 7))
                        except ValueError:
                            converted.append(item)
                return ",".join(converted)
            try:
                return str((int(dow) - 1) % 7)
            except ValueError:
                return dow

        return f"{minute} {hour} {day} {month} {_convert_dow(weekday)}"

    # ------------------------------------------------------------------
    # Job management
    # ------------------------------------------------------------------

    def add_job(
        self,
        job_id: str,
        chat_id: str,
        message: str,
        cron_expression: str,
    ) -> Dict[str, str]:
        is_valid, err = self.validate_cron_expression(cron_expression)
        if not is_valid:
            raise ValueError(f"Invalid cron format: {cron_expression}. {err}")

        aps_expr = self._convert_cron_to_apscheduler_format(cron_expression)

        try:
            trigger = CronTrigger.from_crontab(aps_expr, timezone=WARSAW_TZ)
            self.scheduler.add_job(
                self.callback_func,
                trigger,
                args=[chat_id, message],
                id=job_id,
                replace_existing=True,
            )
            description = f"Cron: {cron_expression} (Europe/Warsaw)"
            return {"expression": cron_expression, "description": description}
        except Exception as e:
            logger.error("Error adding job %s: %s", job_id, e)
            raise ValueError(f"Failed to create trigger: {e}") from e

    def pause_job(self, job_id: str) -> bool:
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info("Job %s paused (removed).", job_id)
                return True
            return False
        except Exception as e:
            logger.error("Error pausing job %s: %s", job_id, e)
            return False

    def resume_job(
        self, job_id: str, cron_expression: str, chat_id: str, message: str
    ) -> bool:
        try:
            self.add_job(job_id, chat_id, message, cron_expression)
            logger.info("Job %s resumed.", job_id)
            return True
        except Exception as e:
            logger.error("Error resuming job %s: %s", job_id, e)
            return False

    def delete_job(self, job_id: str) -> bool:
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            return True
        except Exception as e:
            logger.error("Error deleting job %s: %s", job_id, e)
            return False

