"""
Schedule Manager Module for Telegram Bot
Uses Groq API (free) to parse natural language into cron expressions
"""

import re
from typing import Optional, Dict
from groq import Groq
from config import GROQ_TOKEN


class ScheduleManager:
    """Manager for creating and parsing schedule expressions using AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Schedule Manager with Groq API
        
        Args:
            api_key: Groq API key (if None, reads from GROQ_API_KEY env variable)
        """
        self.client = Groq(
            api_key=api_key or GROQ_TOKEN
        )
    
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
        prompt = f"""Convert the following schedule description into a cron expression.

Text: "{schedule_text}"

Return ONLY the cron expression in format: minute hour day month day_of_week

Examples:
- "every 15 minutes" → */15 * * * *
- "every day at 9 AM" → 0 9 * * *
- "every Monday at 10:30" → 30 10 * * 1
- "first day of month at midnight" → 0 0 1 * *
- "every hour" → 0 * * * *

Return only the cron expression, no explanations."""

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
            
            # Remove potential markdown code blocks
            cron_expression = re.sub(r'```.*?```', '', cron_expression, flags=re.DOTALL)
            cron_expression = cron_expression.strip()
            
            # Validate cron format (must have 5 parts)
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError(f"Invalid cron format: {cron_expression}")
            
            return cron_expression
            
        except Exception as e:
            raise Exception(f"Failed to parse schedule: {str(e)}")