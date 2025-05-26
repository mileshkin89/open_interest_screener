# config

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).parent

load_dotenv()


class AppConfig(BaseSettings):
    DB_PATH: Path = BASE_DIR / "storage" / "signals.db"
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    TG_BOT_API_KEY: str = os.getenv("TG_BOT_API_KEY")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8"
    )


config = AppConfig()
