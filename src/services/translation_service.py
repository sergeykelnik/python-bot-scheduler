"""
Service module for handling translations and localization.
Loads translation strings from JSON files.
"""

import json
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_LANG = 'ru'

class TranslationService:
    """Load and translate button labels and messages from locale/*.json files."""

    def __init__(self, locales_dir: str = 'locales', default_lang: str = DEFAULT_LANG):
        """
        Initialize the Translation Service.
        
        Args:
            locales_dir: Directory containing locale JSON files.
            default_lang: Fallback language code.
        """
        self.locales_dir = locales_dir
        self.default_lang = default_lang
        self._cache: Dict[str, Dict[str, str]] = {}
        
        # Preload all available languages
        if os.path.exists(self.locales_dir) and os.path.isdir(self.locales_dir):
            for fname in os.listdir(self.locales_dir):
                if fname.endswith('.json'):
                    lang = os.path.splitext(fname)[0]
                    try:
                        self._load_lang_file(lang)
                    except Exception as e:
                        logger.error(f"Failed to load language file {fname}: {e}")
        else:
            logger.warning(f"Locales directory '{self.locales_dir}' not found.")

    def _load_lang_file(self, lang: str):
        """Load a single language file into cache."""
        path = os.path.join(self.locales_dir, f"{lang}.json")
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            self._cache[lang] = data
        except Exception as e:
            logger.error(f"Error reading locale file {path}: {e}")
            raise

    def get_button(self, key: str, lang: str = None) -> str:
        """
        Get translated button text; fallback to default language or key itself.
        
        Args:
            key: Translation key.
            lang: Language code (optional).
            
        Returns:
            Translated string.
        """
        if lang is None:
            lang = self.default_lang
        if lang not in self._cache:
            lang = self.default_lang
        return self._cache.get(lang, {}).get(key, key)

    def get_message(self, key: str, lang: str = None) -> str:
        """
        Get translated message text; fallback to default language or key itself.
        
        Args:
            key: Translation key.
            lang: Language code (optional).
        
        Returns:
            Translated string.
        """
        if lang is None:
            lang = self.default_lang
        if lang not in self._cache:
            lang = self.default_lang
        return self._cache.get(lang, {}).get(key, key)

    def available_languages(self) -> List[str]:
        """
        Return list of available language codes.
        
        Returns:
            List of language codes (e.g. ['en', 'ru']).
        """
        return list(self._cache.keys())
