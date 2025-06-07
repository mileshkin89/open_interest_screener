"""
config.py

This module defines application-level configuration using `pydantic-settings` for type-safe
and flexible environment-based settings.

Environment variables are loaded from a `.env` file at startup using `python-dotenv`.
Useful constants such as database and log file paths are also defined here.

Usage:
    from config import config
    print(config.TG_BOT_API_KEY)
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).parent.parent

load_dotenv()


class AppConfig(BaseSettings):
    """
    Application configuration settings.

    Attributes:
        TG_BOT_API_KEY (str): Telegram bot API key, loaded from the environment.
        DB_PATH (Path): Path to the SQLite database file used for storing user settings and signal history.
        LOG_PATH (Path): Path to the application log file.

    Configuration is automatically loaded from a `.env` file if present.
    """
    TG_BOT_API_KEY: str = os.getenv("TG_BOT_API_KEY")

    DB_PATH: Path = BASE_DIR / "storage" / "signals.db"

    LOG_PATH: Path = BASE_DIR / "logs" / "app.log"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8"
    )

# Singleton config instance used throughout the application
config = AppConfig()

