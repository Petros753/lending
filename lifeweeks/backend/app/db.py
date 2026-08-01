"""Доступ к Postgres через asyncpg. Пул один на процесс."""

from __future__ import annotations

import logging
from datetime import date, time
from pathlib import Path
from typing import Any, Iterable, Optional

import asyncpg

from .config import BASE_DIR, get_settings

log = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def init_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = await asyncpg.create_pool(
            settings.database_url, min_size=1, max_size=10, command_timeout=30
        )
        log.info("postgres pool created")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("пул не инициализирован — вызовите init_pool()")
    return _pool


async def run_migrations() -> None:
    """Прогоняет все .sql из migrations/ по порядку имён."""
    migrations_dir = Path(BASE_DIR) / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))
    async with pool().acquire() as conn:
        for path in files:
            log.info("applying migration %s", path.name)
            await conn.execute(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# users
# --------------------------------------------------------------------------

USER_COLUMNS = (
    "telegram_id, birth_date, username, first_name, language_code, timezone, "
    "daily_time, weekly_time, notifications, created_at, updated_at"
)


async def upsert_user(
    telegram_id: int,
    *,
    username: str | None = None,
    first_name: str | None = None,
    language_code: str | None = None,
) -> asyncpg.Record:
    """Создаёт пользователя или обновляет профильные поля из Telegram.

    Профильные поля перетираются только непустыми значениями, чтобы
    отсутствующий в initData username не стирал уже сохранённый.
    """
    settings = get_settings()
    async with pool().acquire() as conn:
        return await conn.fetchrow(
            f"""
            INSERT INTO users (telegram_id, username, first_name, language_code, timezone,
                               daily_time, weekly_time)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (telegram_id) DO UPDATE SET
                username      = COALESCE(EXCLUDED.username, users.username),
                first_name    = COALESCE(EXCLUDED.first_name, users.first_name),
                language_code = COALESCE(EXCLUDED.language_code, users.language_code)
            RETURNING {USER_COLUMNS}
            """,
            telegram_id,
            username,
            first_name,
            language_code,
            settings.default_timezone,
            settings.daily_prompt_time,
            settings.weekly_report_time,
        )


async def get_user(telegram_id: int) -> asyncpg.Record | None:
    async with pool().acquire() as conn:
        return await conn.fetchrow(
            f"SELECT {USER_COLUMNS} FROM users WHERE telegram_id = $1", telegram_id
        )


async def set_birth_date(telegram_id: int, birth_date: date) -> asyncpg.Record | None:
    async with pool().acquire() as conn:
        return await conn.fetchrow(
            f"UPDATE users SET birth_date = $2 WHERE telegram_id = $1 RETURNING {USER_COLUMNS}",
            telegram_id,
            birth_date,
        )


async def update_settings(
    telegram_id: int,
    *,
    timezone: str | None = None,
    daily_time: time | None = None,
    weekly_time: time | None = None,
    notifications: bool | None = None,
) -> asyncpg.Record | None:
    sets: list[str] = []
    args: list[Any] = [telegram_id]
    for column, value in (
        ("timezone", timezone),
        ("daily_time", daily_time),
        ("weekly_time", weekly_time),
        ("notifications", notifications),
    ):
        if value is not None:
            args.append(value)
            sets.append(f"{column} = ${len(args)}")
    if not sets:
        return await get_user(telegram_id)
    async with pool().acquire() as conn:
        return await conn.fetchrow(
            f"UPDATE users SET {', '.join(sets)} WHERE telegram_id = $1 "
            f"RETURNING {USER_COLUMNS}",
            *args,
        )


async def users_for_notification() -> list[asyncpg.Record]:
    """Все, кому в принципе можно слать: есть дата рождения и включены уведомления."""
    async with pool().acquire() as conn:
        return await conn.fetch(
            "SELECT telegram_id, birth_date, first_name, timezone, daily_time, weekly_time "
            "FROM users WHERE notifications AND birth_date IS NOT NULL"
        )


# --------------------------------------------------------------------------
# daily_checkins
# --------------------------------------------------------------------------


async def set_checkin(
    user_id: int, day: date, rating: str, source: str = "bot"
) -> asyncpg.Record:
    async with pool().acquire() as conn:
        return await conn.fetchrow(
            """
            INSERT INTO daily_checkins (user_id, day, rating, source)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, day) DO UPDATE SET
                rating = EXCLUDED.rating,
                source = EXCLUDED.source
            RETURNING id, user_id, day, rating, source
            """,
            user_id,
            day,
            rating,
            source,
        )


async def get_checkins(
    user_id: int, date_from: date, date_to: date
) -> list[asyncpg.Record]:
    """Чек-ины в интервале включительно, по возрастанию даты."""
    async with pool().acquire() as conn:
        return await conn.fetch(
            "SELECT day, rating FROM daily_checkins "
            "WHERE user_id = $1 AND day BETWEEN $2 AND $3 ORDER BY day",
            user_id,
            date_from,
            date_to,
        )


async def get_checkin(user_id: int, day: date) -> asyncpg.Record | None:
    async with pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT day, rating FROM daily_checkins WHERE user_id = $1 AND day = $2",
            user_id,
            day,
        )


async def recent_checkins(user_id: int, since: date) -> list[asyncpg.Record]:
    """Чек-ины начиная с даты — используется для подсчёта серии дней подряд."""
    async with pool().acquire() as conn:
        return await conn.fetch(
            "SELECT day, rating FROM daily_checkins "
            "WHERE user_id = $1 AND day >= $2 ORDER BY day DESC",
            user_id,
            since,
        )


async def count_checkins(user_id: int) -> int:
    async with pool().acquire() as conn:
        return await conn.fetchval(
            "SELECT count(*) FROM daily_checkins WHERE user_id = $1", user_id
        )


# --------------------------------------------------------------------------
# week_ratings (совместимость со старым фронтом)
# --------------------------------------------------------------------------


async def set_week_rating(user_id: int, week_start: date, rating: str) -> None:
    async with pool().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO week_ratings (user_id, week_start, rating)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, week_start) DO UPDATE SET rating = EXCLUDED.rating
            """,
            user_id,
            week_start,
            rating,
        )


async def get_week_ratings(user_id: int) -> list[asyncpg.Record]:
    async with pool().acquire() as conn:
        return await conn.fetch(
            "SELECT week_start, rating FROM week_ratings WHERE user_id = $1 "
            "ORDER BY week_start",
            user_id,
        )


# --------------------------------------------------------------------------
# notifications_log
# --------------------------------------------------------------------------


async def claim_notification(user_id: int, kind: str, target_date: date) -> bool:
    """Резервирует право отправить уведомление.

    Возвращает True ровно один раз для тройки (user, kind, target_date) —
    вставка выполняется до отправки, поэтому гонка тиков планировщика
    или рестарт сервиса не приводят к дублю сообщения.
    """
    async with pool().acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO notifications_log (user_id, kind, target_date)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, kind, target_date) DO NOTHING
            RETURNING id
            """,
            user_id,
            kind,
            target_date,
        )
        return row is not None


async def release_notification(user_id: int, kind: str, target_date: date) -> None:
    """Откатывает резерв, если отправка провалилась по временной причине."""
    async with pool().acquire() as conn:
        await conn.execute(
            "DELETE FROM notifications_log WHERE user_id = $1 AND kind = $2 "
            "AND target_date = $3",
            user_id,
            kind,
            target_date,
        )


def records_to_dicts(rows: Iterable[asyncpg.Record]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]
