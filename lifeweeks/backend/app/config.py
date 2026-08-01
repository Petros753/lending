"""Конфигурация сервиса. Читается из .env рядом с backend/."""

from __future__ import annotations

from datetime import time
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


def _parse_hhmm(value: str | time) -> time:
    if isinstance(value, time):
        return value
    hours, _, minutes = value.strip().partition(":")
    return time(hour=int(hours), minute=int(minutes or 0))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    bot_username: str = "lifeweeks_bot"
    webapp_url: str = "https://lifeweeks.pukikuki.ru"

    database_url: str

    api_host: str = "127.0.0.1"
    api_port: int = 5678

    default_timezone: str = "Europe/Moscow"
    daily_prompt_time: time = time(20, 0)
    weekly_report_time: time = time(9, 0)
    scheduler_tick_minutes: int = 5

    allow_insecure_auth: bool = False
    init_data_ttl: int = 86400
    log_level: str = "INFO"

    @field_validator("daily_prompt_time", "weekly_report_time", mode="before")
    @classmethod
    def _times(cls, v):
        return _parse_hhmm(v)

    @field_validator("scheduler_tick_minutes")
    @classmethod
    def _tick(cls, v: int) -> int:
        if v < 1 or v > 60 or 60 % v != 0:
            raise ValueError("SCHEDULER_TICK_MINUTES должен быть делителем 60")
        return v

    @property
    def webapp_link(self) -> str:
        """Ссылка, открывающая Mini App из сообщения бота."""
        return f"https://t.me/{self.bot_username}?startapp=report"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
