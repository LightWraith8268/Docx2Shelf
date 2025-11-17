"""
Settings and configuration management for Docx2Shelf.

This module provides a unified settings system for both user preferences
and enterprise configuration, with GUI and CLI interfaces.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    from platformdirs import user_config_dir, user_data_dir
except ImportError:
    # Fallback for systems without platformdirs
    def user_config_dir(appname: str, appauthor: str = None) -> str:
        import os

        if os.name == "nt":  # Windows
            return os.path.expandvars(f"%APPDATA%\\{appname}")
        elif os.name == "posix":  # macOS/Linux
            return os.path.expanduser(f"~/.config/{appname}")
        return f".{appname}"

    def user_data_dir(appname: str, appauthor: str = None) -> str:
        import os

        if os.name == "nt":  # Windows
            return os.path.expandvars(f"%LOCALAPPDATA%\\{appname}")
        elif os.name == "posix":  # macOS/Linux
            return os.path.expanduser(f"~/.local/share/{appname}")
        return f".{appname}"


from .enterprise import EnterpriseConfig

logger = logging.getLogger(__name__)


@dataclass
class ConversionDefaults:
    """Default settings for EPUB conversion."""

    css_theme: str = "serif"
    language: str = "en"
    validate_epub: bool = True
    image_max_width: int = 1200
    accessibility_features: bool = True
    chapter_detection: str = "auto"  # auto, h1, h2, pagebreak
    include_toc: bool = True
    include_cover: bool = True
    drm_free: bool = True


@dataclass
class UIPreferences:
    """User interface preferences."""

    remember_last_directory: bool = True
    auto_fill_metadata: bool = True
    show_advanced_options: bool = False
    theme: str = "system"  # light, dark, system
    font_size: str = "medium"  # small, medium, large
    remember_window_size: bool = True
    confirm_overwrite: bool = True
    show_tooltips: bool = True


@dataclass
class FileDefaults:
    """Default file and directory settings."""

    last_input_directory: Optional[str] = None
    last_output_directory: Optional[str] = None
    default_output_directory: Optional[str] = None
    auto_generate_output_name: bool = True
    backup_original: bool = False
    temp_directory: Optional[str] = None


@dataclass
class AIDetectionSettings:
    """AI chapter detection settings."""

    # General AI settings
    confidence_threshold: float = 0.7
    min_chapter_length: int = 500
    enable_heuristics: bool = True
    combine_methods: bool = True

    # Remote AI settings
    use_free_api: bool = True
    api_key: str = ""
    model: str = "gpt-3.5-turbo"

    # Local LLM settings
    use_local_llm: bool = False
    local_llm_endpoint: str = "http://localhost:11434"
    local_llm_model: str = "llama2"
    local_llm_timeout: int = 30
    local_llm_max_tokens: int = 1000


@dataclass
class AdvancedSettings:
    """Advanced application settings."""

    enable_logging: bool = True
    log_level: str = "INFO"
    max_log_files: int = 5
    enable_crash_reporting: bool = True
    check_for_updates: bool = True
    auto_update: bool = False
    enable_telemetry: bool = False
    concurrent_jobs: int = 2


@dataclass
class ApplicationSettings:
    """Complete application settings."""

    conversion_defaults: ConversionDefaults = field(default_factory=ConversionDefaults)
    ui_preferences: UIPreferences = field(default_factory=UIPreferences)
    file_defaults: FileDefaults = field(default_factory=FileDefaults)
    advanced_settings: AdvancedSettings = field(default_factory=AdvancedSettings)
    ai_detection: AIDetectionSettings = field(default_factory=AIDetectionSettings)
    enterprise_config: Optional[EnterpriseConfig] = None
    version: str = "1.0"


class SettingsManager:
    """Manages application settings and enterprise configuration."""

    def __init__(self, app_name: str = "Docx2Shelf"):
        self.app_name = app_name
        self.config_dir = Path(user_config_dir(app_name))
        self.data_dir = Path(user_data_dir(app_name))

        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.settings_file = self.config_dir / "settings.json"
        self.enterprise_file = self.config_dir / "enterprise.json"

        self._settings: Optional[ApplicationSettings] = None
        self._callbacks: List[callable] = []

    @property
    def settings(self) -> ApplicationSettings:
        """Get current settings, loading from disk if needed."""
        if self._settings is None:
            self._settings = self.load_settings()
        return self._settings

    def load_settings(self) -> ApplicationSettings:
        """Load settings from disk."""
        settings = ApplicationSettings()

        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Update settings with loaded data
                if "conversion_defaults" in data:
                    settings.conversion_defaults = ConversionDefaults(**data["conversion_defaults"])
                if "ui_preferences" in data:
                    settings.ui_preferences = UIPreferences(**data["ui_preferences"])
                if "file_defaults" in data:
                    settings.file_defaults = FileDefaults(**data["file_defaults"])
                if "advanced_settings" in data:
                    settings.advanced_settings = AdvancedSettings(**data["advanced_settings"])
                if "ai_detection" in data:
                    settings.ai_detection = AIDetectionSettings(**data["ai_detection"])
                if "version" in data:
                    settings.version = data["version"]

            except Exception as e:
                logger.warning(f"Could not load settings: {e}")

        # Load enterprise config if available
        if self.enterprise_file.exists():
            try:
                with open(self.enterprise_file, "r", encoding="utf-8") as f:
                    enterprise_data = json.load(f)
                settings.enterprise_config = EnterpriseConfig(**enterprise_data)
            except Exception as e:
                logger.warning(f"Could not load enterprise config: {e}")

        return settings

    def save_settings(self, settings: Optional[ApplicationSettings] = None) -> None:
        """Save settings to disk."""
        if settings is None:
            settings = self.settings

        try:
            # Save main settings
            settings_data = {
                "conversion_defaults": asdict(settings.conversion_defaults),
                "ui_preferences": asdict(settings.ui_preferences),
                "file_defaults": asdict(settings.file_defaults),
                "advanced_settings": asdict(settings.advanced_settings),
                "ai_detection": asdict(settings.ai_detection),
                "version": settings.version,
            }

            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)

            # Save enterprise config separately if it exists
            if settings.enterprise_config:
                enterprise_data = asdict(settings.enterprise_config)
                with open(self.enterprise_file, "w", encoding="utf-8") as f:
                    json.dump(enterprise_data, f, indent=2, ensure_ascii=False)

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(settings)
                except Exception as e:
                    logger.warning(f"Settings callback failed: {e}")

        except Exception as e:
            logger.error(f"Could not save settings: {e}")
            raise

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self._settings = ApplicationSettings()
        self.save_settings()

    def export_settings(self, export_path: Path) -> None:
        """Export settings to a file."""
        settings_data = asdict(self.settings)
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)

    def import_settings(self, import_path: Path, merge: bool = True) -> None:
        """Import settings from a file."""
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if merge:
            # Merge with existing settings
            current = asdict(self.settings)
            self._merge_settings(current, data)
            self._settings = self._dict_to_settings(current)
        else:
            # Replace all settings
            self._settings = self._dict_to_settings(data)

        self.save_settings()

    def add_callback(self, callback: callable) -> None:
        """Add a callback function to be called when settings change."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: callable) -> None:
        """Remove a callback function."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _merge_settings(self, target: dict, source: dict) -> None:
        """Recursively merge settings dictionaries."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_settings(target[key], value)
            else:
                target[key] = value

    def _dict_to_settings(self, data: dict) -> ApplicationSettings:
        """Convert dictionary to ApplicationSettings object."""
        settings = ApplicationSettings()

        if "conversion_defaults" in data:
            settings.conversion_defaults = ConversionDefaults(**data["conversion_defaults"])
        if "ui_preferences" in data:
            settings.ui_preferences = UIPreferences(**data["ui_preferences"])
        if "file_defaults" in data:
            settings.file_defaults = FileDefaults(**data["file_defaults"])
        if "advanced_settings" in data:
            settings.advanced_settings = AdvancedSettings(**data["advanced_settings"])
        if "ai_detection" in data:
            settings.ai_detection = AIDetectionSettings(**data["ai_detection"])
        if "enterprise_config" in data and data["enterprise_config"]:
            settings.enterprise_config = EnterpriseConfig(**data["enterprise_config"])
        if "version" in data:
            settings.version = data["version"]

        return settings


# Global settings manager instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def get_settings() -> ApplicationSettings:
    """Get current application settings."""
    return get_settings_manager().settings


def save_settings(settings: Optional[ApplicationSettings] = None) -> None:
    """Save application settings."""
    get_settings_manager().save_settings(settings)
