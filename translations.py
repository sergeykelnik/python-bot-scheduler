"""Simple translator for button labels from locale JSON files"""
import json
import os
from typing import Dict

DEFAULT_LANG = 'ru'


class Translator:
    """Load and translate button labels from locale/*.json files."""

    def __init__(self, locales_dir: str = 'locales', default_lang: str = DEFAULT_LANG):
        self.locales_dir = locales_dir
        self.default_lang = default_lang
        self._cache: Dict[str, Dict[str, str]] = {}
        # Preload all available languages
        if os.path.isdir(self.locales_dir):
            for fname in os.listdir(self.locales_dir):
                if fname.endswith('.json'):
                    lang = os.path.splitext(fname)[0]
                    try:
                        self._load_lang_file(lang)
                    except Exception:
                        pass

    def _load_lang_file(self, lang: str):
        """Load a single language file into cache."""
        path = os.path.join(self.locales_dir, f"{lang}.json")
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        self._cache[lang] = data

    def get_button(self, key: str, lang: str = None) -> str:
        """Get translated button text; fallback to default language or key itself."""
        if lang is None:
            lang = self.default_lang
        if lang not in self._cache:
            lang = self.default_lang
        return self._cache.get(lang, {}).get(key, key)

    def get_message(self, key: str, lang: str = None) -> str:
        """Get translated message text; fallback to default language or key itself."""
        if lang is None:
            lang = self.default_lang
        if lang not in self._cache:
            lang = self.default_lang
        return self._cache.get(lang, {}).get(key, key)

    def available_languages(self):
        """Return list of available language codes."""
        return list(self._cache.keys())
