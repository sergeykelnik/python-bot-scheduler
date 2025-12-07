"""
Scheduler Service module.
Manages APScheduler background tasks and cron expression validation.
"""

import logging
from typing import Dict, Any, Optional, Tuple, Set
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job
from src.core.config import WARSAW_TZ

logger = logging.getLogger(__name__)

class SchedulerService:
    """Service to manage background scheduled jobs."""
    
    # Valid day names (case-insensitive) for cron validation
    VALID_DAY_NAMES = {'SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', '0', '1', '2', '3', '4', '5', '6', '7'}
    # Valid month names (case-insensitive)
    VALID_MONTH_NAMES = {'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
                        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'}

    def __init__(self, callback_func):
        """
        Initialize Scheduler Service.
        
        Args:
            callback_func: Function to call when a job triggers. 
                           Signature: (chat_id: str, message: str)
        """
        self.scheduler = BackgroundScheduler(timezone=WARSAW_TZ)
        self.scheduled_jobs: Dict[str, Dict[str, Any]] = {}
        self.callback_func = callback_func

    def start(self):
        """Start the background scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started.")

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown.")

    # --- Cron Validation and Conversion Logic ---

    def _validate_cron_field(self, field: str, field_type: str) -> bool:
        """
        Validate individual cron field.
        
        Args:
            field: The cron field to validate.
            field_type: 'minute'|'hour'|'day'|'month'|'weekday'.
            
        Returns:
            True if valid, False otherwise.
        """
        if not field:
            return False
        
        # Wildcards and step values are always valid
        if field == '*':
            return True
        
        # Handle step expressions (e.g., */5, 0-23/2)
        if '/' in field:
            parts = field.split('/')
            if len(parts) != 2:
                return False
            base, step = parts
            try:
                int(step)  # Step must be a number
            except ValueError:
                return False
            if base == '*':
                return True
            # Validate the base part recursively
            return self._validate_cron_field(base, field_type)
        
        # Handle ranges (e.g., 1-5, MON-FRI)
        if '-' in field:
            parts = field.split('-')
            if len(parts) != 2:
                return False
            for part in parts:
                if part and not part[0].isdigit() and part.upper() not in (self.VALID_DAY_NAMES | self.VALID_MONTH_NAMES):
                    try:
                        int(part)
                    except ValueError:
                        return False
            return True
        
        # Handle lists (e.g., 1,3,5, MON,WED,FRI)
        if ',' in field:
            parts = field.split(',')
            for part in parts:
                if not self._validate_cron_field(part, field_type):
                    return False
            return True
        
        # Single value - check if valid
        try:
            int(field)
            return True
        except ValueError:
            # Check if it's a valid day or month name
            if field.upper() in (self.VALID_DAY_NAMES | self.VALID_MONTH_NAMES):
                return True
            return False

    def validate_cron_expression(self, expression: str) -> Tuple[bool, str]:
        """
        Comprehensive validation of cron expression.
        
        Args:
            expression: The cron expression to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        expression = expression.strip()
        parts = expression.split()
        
        # Must have exactly 5 fields
        if len(parts) != 5:
            return False, f"Cron must have 5 fields (minute hour day month weekday), got {len(parts)}"
        
        minute, hour, day, month, weekday = parts
        
        # Basic range validation
        field_specs = [
            (minute, 'minute', 0, 59),
            (hour, 'hour', 0, 23),
            (day, 'day', 1, 31),
            (month, 'month', 1, 12),
            (weekday, 'weekday', 0, 7)
        ]
        
        for field, name, _, _ in field_specs:
            if not self._validate_cron_field(field, name):
                return False, f"Invalid {name} field: {field}"
        
        return True, ""

    def _convert_cron_to_apscheduler_format(self, expression: str) -> str:
        """
        Convert standard Unix cron day_of_week (0=Sunday) to APScheduler format (0=Monday).
        APScheduler uses: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
        Standard cron uses: 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday
        """
        parts = expression.split()
        if len(parts) != 5:
            return expression
        
        minute, hour, day, month, weekday = parts
        
        if weekday in ('*', '?'):
            return expression
        
        if any(name in weekday.upper() for name in ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']):
            return expression
            
        def convert_dow(dow_str: str) -> str:
            if dow_str == '*' or dow_str == '?':
                return dow_str
            
            # Handle ranges
            if '-' in dow_str and ',' not in dow_str:
                parts_range = dow_str.split('-')
                try:
                    start = int(parts_range[0])
                    end = int(parts_range[1])
                    converted_start = (start - 1) % 7
                    converted_end = (end - 1) % 7
                    if converted_start <= converted_end:
                        return f"{converted_start}-{converted_end}"
                    else:
                        return f"{converted_start},0-{converted_end}"
                except (ValueError, IndexError):
                    return dow_str
            
            # Handle lists
            if ',' in dow_str:
                items = dow_str.split(',')
                converted = []
                for item in items:
                    if '-' in item:
                        converted.append(convert_dow(item))
                    else:
                        try:
                            val = int(item)
                            converted.append(str((val - 1) % 7))
                        except ValueError:
                            converted.append(item)
                return ','.join(converted)
            
            # Handle single numeric values
            try:
                val = int(dow_str)
                return str((val - 1) % 7)
            except ValueError:
                return dow_str
        
        weekday_converted = convert_dow(weekday)
        return f"{minute} {hour} {day} {month} {weekday_converted}"

    # --- Job Management ---

    def add_job(self, job_id: str, chat_id: str, message: str, cron_expression: str) -> Dict[str, str]:
        """
        Add a cron-based job to the scheduler.
        
        Args:
            job_id: Unique Job ID.
            chat_id: Target Chat ID.
            message: Message to send.
            cron_expression: Cron expression string.
            
        Returns:
            Dictionary with schedule details.
            
        Raises:
            ValueError: If cron expression is invalid.
        """
        is_valid, error_msg = self.validate_cron_expression(cron_expression)
        if not is_valid:
            raise ValueError(f"Invalid cron format: {cron_expression}. {error_msg}")
        
        aps_expression = self._convert_cron_to_apscheduler_format(cron_expression)
        
        try:
            trigger = CronTrigger.from_crontab(aps_expression, timezone=WARSAW_TZ)
            self.scheduler.add_job(
                self.callback_func,
                trigger,
                args=[chat_id, message],
                id=job_id,
                replace_existing=True
            )
            
            description = f"Cron: {cron_expression} (Europe/Warsaw)"
            schedule_data = {'expression': cron_expression, 'description': description}
            
            # Update memory cache
            # Note: The full job structure is usually managed by the caller/storage, 
            # here we might just track that it exists in scheduler or rely on APScheduler.
            # But the existing logic maintained a separate `scheduled_jobs` dict.
            # We will return the data and let the caller manage the comprehensive state if needed,
            # but for consistency with previous design, we can store basic info here.
            return schedule_data

        except Exception as e:
            logger.error(f"Error adding job {job_id}: {e}")
            raise ValueError(f"Failed to create trigger: {str(e)}")

    def pause_job(self, job_id: str) -> bool:
        """Pause a running job."""
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Job {job_id} paused (removed from scheduler).")
                return True
            return False # Job wasn't running
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False

    def resume_job(self, job_id: str, cron_expression: str, chat_id: str, message: str) -> bool:
        """Resume a job by re-adding it."""
        try:
            self.add_job(job_id, chat_id, message, cron_expression)
            logger.info(f"Job {job_id} resumed.")
            return True
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False

    def delete_job(self, job_id: str) -> bool:
        """Delete a job permanently from scheduler."""
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False
