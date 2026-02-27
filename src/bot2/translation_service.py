"""
Translation / i18n service.
Loads translation strings from locale JSON files.
"""

import json
import logging
import os
from typing import Dict, List

logger = logging.getLogger(__name__)

DEFAULT_LANG = "ru"


class TranslationService:
    """Load and serve translated button labels and messages from locales/*.json."""

    def __init__(self, locales_dir: str = "locales", default_lang: str = DEFAULT_LANG):
        self.locales_dir = locales_dir
        self.default_lang = default_lang
        self._cache: Dict[str, Dict[str, str]] = {}

        if os.path.exists(self.locales_dir) and os.path.isdir(self.locales_dir):
            for fname in os.listdir(self.locales_dir):
                if fname.endswith(".json"):
                    lang = os.path.splitext(fname)[0]
                    try:
                        self._load(lang)
                    except Exception as e:
                        logger.error("Failed to load language file %s: %s", fname, e)
        else:
            logger.warning("Locales directory '%s' not found.", self.locales_dir)

    def _load(self, lang: str) -> None:
        path = os.path.join(self.locales_dir, f"{lang}.json")
        with open(path, "r", encoding="utf-8") as fh:
            self._cache[lang] = json.load(fh)

    def _resolve_lang(self, lang: str | None) -> str:
        if lang is None or lang not in self._cache:
            return self.default_lang
        return lang

    def get_message(self, key: str, lang: str | None = None) -> str:
        lang = self._resolve_lang(lang)
        return self._cache.get(lang, {}).get(key, key)

    def get_button(self, key: str, lang: str | None = None) -> str:
        lang = self._resolve_lang(lang)
        return self._cache.get(lang, {}).get(key, key)

    def available_languages(self) -> List[str]:
        return list(self._cache.keys())

