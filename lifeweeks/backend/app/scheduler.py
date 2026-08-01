"""Планировщик рассылок на APScheduler.

Живёт в одном процессе с ботом и API — отдельного крона не требуется.

Время рассылки у каждого пользователя своё (его таймзона + его настройка
часа), поэтому здесь нет «задачи на 20:00». Вместо этого раз в
SCHEDULER_TICK_MINUTES минут мы проходим по пользователям и проверяем,
наступило ли *у них* нужное локальное время.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from . import bot as bot_module
from . import db, lifeweeks
from .config import get_settings

log = logging.getLogger(__name__)

#: Насколько поздно ещё имеет смысл досылать пропущенное уведомление.
#: Защищает от «тишины», если сервис лежал ровно в свой тик, и одновременно
#: не даёт прислать вечерний вопрос в три часа ночи.
DAILY_GRACE = timedelta(hours=3)
WEEKLY_GRACE = timedelta(hours=6)

#: Пауза между отправками — Telegram ограничивает ~30 сообщений в секунду.
SEND_DELAY = 0.05


def _minutes(value) -> int:
    return value.hour * 60 + value.minute


def _is_due(now: datetime, target, grace: timedelta) -> bool:
    """Пора ли слать: локальное время прошло target, но не позже target+grace."""
    delta = _minutes(now.time()) - _minutes(target)
    return 0 <= delta <= grace.total_seconds() / 60


async def _process_user(bot: Bot, row) -> None:
    now = lifeweeks.local_now(row["timezone"])
    today: date = now.date()

    if row["birth_date"] is None or today < row["birth_date"]:
        return

    # Понедельник: сначала недельный отчёт.
    if now.weekday() == 0 and _is_due(now, row["weekly_time"], WEEKLY_GRACE):
        if await db.claim_notification(row["telegram_id"], "weekly", today):
            ok = await bot_module.send_weekly_report(bot, row, today)
            if not ok:
                await db.release_notification(row["telegram_id"], "weekly", today)
            await asyncio.sleep(SEND_DELAY)

    if _is_due(now, row["daily_time"], DAILY_GRACE):
        if await db.claim_notification(row["telegram_id"], "daily", today):
            ok = await bot_module.send_daily_prompt(bot, row, today)
            if not ok:
                await db.release_notification(row["telegram_id"], "daily", today)
            await asyncio.sleep(SEND_DELAY)


async def tick(bot: Bot) -> None:
    try:
        users = await db.users_for_notification()
    except Exception:  # noqa: BLE001 — БД может быть временно недоступна
        log.exception("не удалось получить список пользователей для рассылки")
        return

    for row in users:
        try:
            await _process_user(bot, row)
        except Exception:  # noqa: BLE001 — один сбойный пользователь не должен
            log.exception("сбой обработки пользователя %s", row["telegram_id"])


def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        tick,
        trigger=IntervalTrigger(minutes=settings.scheduler_tick_minutes),
        args=[bot],
        id="lifeweeks-tick",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
        next_run_time=datetime.now(),
    )
    scheduler.start()
    log.info("scheduler started, tick=%s min", settings.scheduler_tick_minutes)
    return scheduler
