"""
Schedule Manager Module for Telegram Bot
Uses Groq API (free) to parse natural language into cron expressions
"""

import re
import logging
from typing import Optional, Dict
from groq import Groq
from config import GROQ_TOKEN

logger = logging.getLogger(__name__)


class ScheduleManager:
    """Manager for creating and parsing schedule expressions using AI"""
    
    # Valid day names (case-insensitive)
    VALID_DAY_NAMES = {'SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', '0', '1', '2', '3', '4', '5', '6', '7'}
    # Valid month names (case-insensitive)
    VALID_MONTH_NAMES = {'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
                        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'}
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Schedule Manager with Groq API
        
        Args:
            api_key: Groq API key (if None, reads from GROQ_API_KEY env variable)
        """
        self.client = Groq(
            api_key=api_key or GROQ_TOKEN
        )
    
    def _validate_cron_field(self, field: str, field_type: str) -> bool:
        """
        Validate individual cron field.
        
        Args:
            field: The cron field to validate
            field_type: 'minute'|'hour'|'day'|'month'|'weekday'
            
        Returns:
            True if valid, False otherwise
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
    
    def _convert_cron_to_apscheduler_format(self, expression: str) -> str:
        """
        Convert standard Unix cron day_of_week (0=Sunday) to APScheduler format (0=Monday).
        
        APScheduler uses: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
        Standard cron uses: 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday
        
        Args:
            expression: Standard Unix cron expression
            
        Returns:
            APScheduler-compatible cron expression
        """
        parts = expression.split()
        if len(parts) != 5:
            return expression
        
        minute, hour, day, month, weekday = parts
        
        # Only convert numeric day_of_week values, not day names or wildcards
        if weekday in ('*', '?'):
            return expression
        
        # Check if it contains day names (SUN, MON, etc.) - don't convert those
        if any(name in weekday.upper() for name in ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']):
            return expression
        
        # Convert standard cron day_of_week to APScheduler format
        # Standard: 0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat
        # APScheduler: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
        
        def convert_dow(dow_str: str) -> str:
            """Convert individual day of week value or expression."""
            if dow_str == '*' or dow_str == '?':
                return dow_str
            
            # Handle ranges (e.g., "0-2" -> "6,0-1" for Sun-Tue)
            if '-' in dow_str and ',' not in dow_str:
                parts_range = dow_str.split('-')
                try:
                    start = int(parts_range[0])
                    end = int(parts_range[1])
                    # Convert range
                    converted_start = (start - 1) % 7
                    converted_end = (end - 1) % 7
                    if converted_start <= converted_end:
                        return f"{converted_start}-{converted_end}"
                    else:
                        # Wrap-around case (e.g., 6-1 becomes Sat-Mon = 5,6,0)
                        return f"{converted_start},0-{converted_end}"
                except (ValueError, IndexError):
                    return dow_str
            
            # Handle lists (e.g., "0,3,5" -> "6,2,4")
            if ',' in dow_str:
                items = dow_str.split(',')
                converted = []
                for item in items:
                    if '-' in item:
                        # Handle range within list
                        converted.append(convert_dow(item))
                    else:
                        try:
                            val = int(item)
                            converted.append(str((val - 1) % 7))
                        except ValueError:
                            converted.append(item)
                return ','.join(converted)
            
            # Handle single numeric values (e.g., "3" -> "2" for Wednesday)
            try:
                val = int(dow_str)
                return str((val - 1) % 7)
            except ValueError:
                # Not a number, might be a step expression like "*/2"
                return dow_str
        
        weekday_converted = convert_dow(weekday)
        return f"{minute} {hour} {day} {month} {weekday_converted}"
    
    def validate_cron_expression(self, expression: str) -> tuple:
        """
        Comprehensive validation of cron expression.
        
        Args:
            expression: The cron expression to validate
            
        Returns:
            Tuple of (is_valid, error_message)
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
        
        for field, name, min_val, max_val in field_specs:
            if not self._validate_cron_field(field, name):
                return False, f"Invalid {name} field: {field}"
        
        return True, ""
    
    def _parse_schedule_with_ai(self, schedule_text: str) -> str:
        """
        Parse schedule text into cron expression using Groq AI
        
        Args:
            schedule_text: Natural language description of schedule
            
        Returns:
            Cron expression string (format: minute hour day month day_of_week)
            
        Raises:
            Exception: If parsing fails or API returns invalid format
        """
        prompt = f"""Convert the following schedule description into a valid cron expression. 
If description is not clear or it's not possible to create valid cron expression, return ONLY an error message starting with "ERROR:".

Text: "{schedule_text}"

Return ONLY a valid cron expression in format: minute hour day month day_of_week

The cron expression must:
- Have exactly 5 fields separated by spaces
- Support standard values: numbers, wildcards (*), ranges (1-5), steps (*/5, 0-23/2), lists (1,3,5)
- Support day names: SUN, MON, TUE, WED, THU, FRI, SAT (and 0-7 for numeric)
- Support month names: JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC (and 1-12 for numeric)

Examples:
- "every 15 minutes" → */15 * * * *
- "every day at 9 AM" → 0 9 * * *
- "every Monday at 10:30" → 30 10 * * MON
- "first day of month at midnight" → 0 0 1 * *
- "every weekday at 8 AM" → 0 8 * * MON-FRI
- "every hour" → 0 * * * *
- "every 30 minutes from 9 to 17" → */30 9-17 * * *

Return ONLY the cron expression (5 fields), no explanations or markdown."""

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            # Extract response text
            cron_expression = completion.choices[0].message.content.strip()
            
            # Check for error response from AI
            if cron_expression.upper().startswith("ERROR:"):
                raise ValueError(cron_expression)
            
            # Remove potential markdown code blocks
            cron_expression = re.sub(r'```.*?```', '', cron_expression, flags=re.DOTALL)
            cron_expression = cron_expression.strip()
            
            # Validate cron format
            is_valid, error_msg = self.validate_cron_expression(cron_expression)
            if not is_valid:
                raise ValueError(f"Invalid cron from AI: {cron_expression}. {error_msg}")
            
            logger.info(f"Successfully parsed schedule '{schedule_text}' to cron: {cron_expression}")
            return cron_expression
            
        except Exception as e:
            logger.error(f"Failed to parse schedule with AI: {str(e)}")
            raise Exception(f"Failed to parse schedule: {str(e)}")