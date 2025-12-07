"""
AI Service module for parsing natural language into cron expressions.
Uses Groq API.
"""

import re
import logging
from typing import Optional, Tuple
from groq import Groq
from src.core.config import GROQ_TOKEN

logger = logging.getLogger(__name__)

class AIService:
    """Service to handle AI interactions."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI Service with Groq API.
        
        Args:
            api_key: Groq API key (optional, defaults to config).
        """
        self.client = Groq(
            api_key=api_key or GROQ_TOKEN
        )
    
    def parse_schedule_to_cron(self, schedule_text: str) -> str:
        """
        Parse schedule text into cron expression using Groq AI.
        
        Args:
            schedule_text: Natural language description of schedule.
            
        Returns:
            Cron expression string (format: minute hour day month day_of_week).
            
        Raises:
            ValueError: If parsing fails or API returns invalid format.
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
- "every 15 minutes" -> */15 * * * *
- "every day at 9 AM" -> 0 9 * * *
- "every Monday at 10:30" -> 30 10 * * MON
- "first day of month at midnight" -> 0 0 1 * *
- "every weekday at 8 AM" -> 0 8 * * MON-FRI
- "every hour" -> 0 * * * *
- "every 30 minutes from 9 to 17" -> */30 9-17 * * *

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
            
            return cron_expression
            
        except Exception as e:
            logger.error(f"Failed to parse schedule with AI: {str(e)}")
            raise ValueError(f"Failed to parse schedule: {str(e)}")
