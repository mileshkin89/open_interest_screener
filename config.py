# config

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).parent

load_dotenv()


class AppConfig(BaseSettings):
    TG_BOT_API_KEY: str = os.getenv("TG_BOT_API_KEY")

    DB_PATH: Path = BASE_DIR / "storage" / "signals.db"

    LOG_PATH: Path = BASE_DIR / "logs" / "app.log"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8"
    )


config = AppConfig()
