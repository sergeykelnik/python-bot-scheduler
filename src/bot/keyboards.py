"""
Inline keyboard builders.
"""

from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.translation_service import TranslationService


def start_keyboard(tr: TranslationService, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr.get_button("btn_lang_en", lang), callback_data="lang:en"),
                InlineKeyboardButton(text=tr.get_button("btn_lang_ru", lang), callback_data="lang:ru"),
            ],
            [InlineKeyboardButton(text=tr.get_button("btn_schedule", lang), callback_data="cmd:schedule")],
            [InlineKeyboardButton(text=tr.get_button("btn_list", lang), callback_data="cmd:list")],
            [InlineKeyboardButton(text=tr.get_button("btn_manage", lang), callback_data="cmd:manage")],
            [InlineKeyboardButton(text=tr.get_button("btn_timezone", lang), callback_data="cmd:timezone")],
            [InlineKeyboardButton(text=tr.get_button("btn_help", lang), callback_data="cmd:help")],
        ]
    )


def help_keyboard(tr: TranslationService, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr.get_button("btn_schedule", lang), callback_data="cmd:schedule"),
                InlineKeyboardButton(text=tr.get_button("btn_list", lang), callback_data="cmd:list"),
                InlineKeyboardButton(text=tr.get_button("btn_manage", lang), callback_data="cmd:manage"),
            ]
        ]
    )


def schedule_step1_keyboard(
    tr: TranslationService, lang: str, has_recent_contacts: bool = False
) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=tr.get_button("btn_me", lang), callback_data="schedule:me")]
    ]
    if has_recent_contacts:
        rows.append(
            [InlineKeyboardButton(text=tr.get_button("btn_saved_contacts", lang), callback_data="schedule:saved_contacts")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def saved_contacts_keyboard(
    tr: TranslationService, lang: str, contacts: List[int]
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=str(c), callback_data=f"schedule:select_contact:{c}")]
        for c in contacts
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def job_manage_keyboard(
    tr: TranslationService, lang: str, job_id: str, is_paused: bool
) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton(text=tr.get_button("btn_edit", lang), callback_data=f"manage:edit:{job_id}"),
    ]
    if is_paused:
        row2 = [
            InlineKeyboardButton(text=tr.get_button("btn_resume", lang), callback_data=f"manage:resume:{job_id}"),
            InlineKeyboardButton(text=tr.get_button("btn_delete", lang), callback_data=f"manage:delete:{job_id}"),
        ]
    else:
        row2 = [
            InlineKeyboardButton(text=tr.get_button("btn_pause", lang), callback_data=f"manage:pause:{job_id}"),
            InlineKeyboardButton(text=tr.get_button("btn_delete", lang), callback_data=f"manage:delete:{job_id}"),
        ]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2])


def confirm_delete_keyboard(
    tr: TranslationService, lang: str, job_id: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr.get_button("btn_confirm_delete", lang),
                    callback_data=f"confirm_delete:{job_id}",
                ),
                InlineKeyboardButton(
                    text=tr.get_button("btn_cancel", lang),
                    callback_data=f"cancel_delete:{job_id}",
                ),
            ]
        ]
    )


def success_keyboard(
    tr: TranslationService, lang: str, job_id: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr.get_button("btn_list", lang), callback_data="cmd:list"),
                InlineKeyboardButton(text=tr.get_button("btn_manage", lang), callback_data="cmd:manage"),
            ],
            [
                InlineKeyboardButton(text=tr.get_button("btn_delete", lang), callback_data=f"manage:delete:{job_id}"),
            ],
        ]
    )


def manage_button(tr: TranslationService, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr.get_button("btn_manage", lang), callback_data="cmd:manage")]
        ]
    )


def cancel_edit_keyboard(tr: TranslationService, lang: str, job_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr.get_button("btn_cancel", lang), callback_data=f"cancel_edit:{job_id}"),
            ]
        ]
    )


def edit_message_keyboard(tr: TranslationService, lang: str, job_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr.get_button("btn_keep_current", lang), callback_data=f"edit_keep:{job_id}"),
            ],
            [
                InlineKeyboardButton(text=tr.get_button("btn_cancel", lang), callback_data=f"cancel_edit:{job_id}"),
            ]
        ]
    )


def timezone_keyboard(tr: TranslationService, lang: str) -> InlineKeyboardMarkup:
    # Common timezones to choose from
    common_tz = ["UTC", "Europe/London", "Europe/Warsaw", "Europe/Moscow", "America/New_York", "Asia/Tokyo", "Asia/Dubai"]
    rows = []
    for i in range(0, len(common_tz), 2):
        row = [InlineKeyboardButton(text=tz, callback_data=f"set_tz:{tz}") for tz in common_tz[i:i+2]]
        rows.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def restart_button(tr: TranslationService, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr.get_button("btn_schedule", lang), callback_data="cmd:schedule")]
        ]
    )

