"""Pydantic-модели запросов и ответов API."""

from __future__ import annotations

# Поле RateDayRequest.date затеняет тип `date` в пространстве имён класса,
# поэтому в аннотациях используются псевдонимы.
from datetime import date as Date, time as Time
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Rating = Literal["good", "neutral", "bad"]

# Фронт исторически шлёт эмодзи/русские подписи — приводим к канону.
RATING_ALIASES = {
    "🙂": "good", "😐": "neutral", "🙁": "bad",
    "good": "good", "neutral": "neutral", "bad": "bad",
    "хорошо": "good", "нейтрально": "neutral", "плохо": "bad",
    "1": "bad", "2": "neutral", "3": "good",
}


def normalize_rating(value: str) -> str:
    key = str(value).strip().lower()
    if key not in RATING_ALIASES:
        raise ValueError(f"неизвестная оценка: {value!r}")
    return RATING_ALIASES[key]


class BirthDateRequest(BaseModel):
    birth_date: Date = Field(alias="birth_date")

    @field_validator("birth_date")
    @classmethod
    def _sane(cls, v: Date) -> Date:
        today = Date.today()
        if v > today:
            raise ValueError("дата рождения в будущем")
        if v.year < 1900:
            raise ValueError("дата рождения раньше 1900 года")
        return v


class RateDayRequest(BaseModel):
    date: Date | None = None
    rating: str

    @field_validator("rating")
    @classmethod
    def _rating(cls, v: str) -> str:
        return normalize_rating(v)


class RateWeekRequest(BaseModel):
    week_start: Date
    rating: str

    @field_validator("rating")
    @classmethod
    def _rating(cls, v: str) -> str:
        return normalize_rating(v)


class SettingsRequest(BaseModel):
    timezone: str | None = None
    daily_time: Time | None = None
    weekly_time: Time | None = None
    notifications: bool | None = None


class UserResponse(BaseModel):
    telegram_id: int
    birth_date: Date | None
    username: str | None
    first_name: str | None
    timezone: str
    daily_time: Time
    weekly_time: Time
    notifications: bool
    today: Date
    life_week: int | None = None
    total_weeks: int | None = None
    age: int | None = None
    today_rating: str | None = None
    checkins_total: int = 0
    streak: int = 0
    is_new: bool = False
