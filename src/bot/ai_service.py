"""
AI Service – async Groq integration for natural-language → cron parsing.
"""

import logging
import re
from typing import Optional

from groq import AsyncGroq

from src.bot.config import GROQ_TOKEN

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = """Convert the following schedule description into a valid cron expression. 
If description is not clear or it's not possible to create valid cron expression, return ONLY an error message starting with "ERROR:".

Text: "{text}"

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


class AIService:
    """Async wrapper around the Groq chat-completions API."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncGroq(api_key=api_key or GROQ_TOKEN)

    async def parse_schedule_to_cron(self, schedule_text: str) -> str:
        """
        Send *schedule_text* to Groq and return a 5-field cron expression.

        Raises:
            ValueError: on API error or when AI cannot parse the text.
        """
        prompt = _PROMPT_TEMPLATE.format(text=schedule_text)

        try:
            completion = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100,
            )

            cron_expression = completion.choices[0].message.content.strip()

            if cron_expression.upper().startswith("ERROR:"):
                raise ValueError(cron_expression)

            # Strip potential markdown fences (```cron\n...\n``` or ```...```)
            fence_match = re.search(r"```(?:\w*\n)?(.*?)```", cron_expression, flags=re.DOTALL)
            if fence_match:
                cron_expression = fence_match.group(1).strip()

            return cron_expression

        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to parse schedule with AI: %s", e)
            raise ValueError(f"Failed to parse schedule: {e}") from e

