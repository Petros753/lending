"""Telegram-бот на aiogram 3.

Регистрация возможна и через Mini App (основной сценарий), и текстом в чате —
пользователи, пришедшие по /start с телефона без открытия веб-вью, не должны
упираться в тупик.
"""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from . import db, lifeweeks
from .config import get_settings

log = logging.getLogger(__name__)
router = Router()

RATING_LABEL = {"good": "🙂 хорошо", "neutral": "😐 нейтрально", "bad": "🙁 плохо"}
RATING_EMOJI = {"good": "🙂", "neutral": "😐", "bad": "🙁"}

# 31.12.1990 / 31-12-1990 / 31 12 1990 / 1990-12-31
_DATE_PATTERNS = (
    (re.compile(r"^(\d{1,2})[.\-/ ](\d{1,2})[.\-/ ](\d{4})$"), ("d", "m", "y")),
    (re.compile(r"^(\d{4})[.\-/ ](\d{1,2})[.\-/ ](\d{1,2})$"), ("y", "m", "d")),
)


def parse_birth_date(text: str) -> date | None:
    cleaned = text.strip()
    for pattern, order in _DATE_PATTERNS:
        match = pattern.match(cleaned)
        if not match:
            continue
        parts = dict(zip(order, (int(g) for g in match.groups())))
        try:
            value = date(parts["y"], parts["m"], parts["d"])
        except ValueError:
            return None
        if value > date.today() or value.year < 1900:
            return None
        return value
    return None


def rating_keyboard(day: date) -> InlineKeyboardMarkup:
    """Кнопки оценки. Дата зашита в callback_data — сообщение вчерашнего дня
    не «переедет» на сегодня, если пользователь нажмёт кнопку утром."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=RATING_EMOJI[rating],
                    callback_data=f"rate:{day.isoformat()}:{rating}",
                )
                for rating in ("good", "neutral", "bad")
            ]
        ]
    )


def webapp_keyboard(text: str = "📊 Открыть отчёт") -> InlineKeyboardMarkup:
    settings = get_settings()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, web_app=WebAppInfo(url=settings.webapp_url))]
        ]
    )


# --------------------------------------------------------------------------
# команды
# --------------------------------------------------------------------------


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    row = await db.upsert_user(
        user.id,
        username=user.username,
        first_name=user.first_name,
        language_code=user.language_code,
    )
    name = row["first_name"] or "друг"

    if row["birth_date"] is None:
        await message.answer(
            f"Привет, {name}! Это <b>LifeWeeks</b> — вся ваша жизнь в неделях.\n\n"
            "Чтобы начать, укажите дату рождения: откройте приложение кнопкой ниже "
            "или просто пришлите её сообщением в формате <code>31.12.1990</code>.",
            reply_markup=webapp_keyboard("🚀 Открыть LifeWeeks"),
        )
        return

    today = lifeweeks.local_today(row["timezone"])
    week = lifeweeks.life_week_number(row["birth_date"], today)
    await message.answer(
        f"С возвращением, {name}! Сейчас идёт <b>{week}-я неделя</b> вашей жизни.\n\n"
        "Каждый вечер я спрошу, как прошёл день, а по понедельникам пришлю отчёт "
        "за прошедшую неделю.",
        reply_markup=webapp_keyboard("🗓 Открыть LifeWeeks"),
    )


@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    """Отметить сегодняшний день, не дожидаясь вечерней рассылки."""
    row = await db.get_user(message.from_user.id)
    if row is None or row["birth_date"] is None:
        await message.answer("Сначала укажите дату рождения — пришлите её сообщением.")
        return
    today = lifeweeks.local_today(row["timezone"])
    existing = await db.get_checkin(message.from_user.id, today)
    prefix = (
        f"Сегодня уже отмечено как {RATING_LABEL[existing['rating']]}. Изменить?\n\n"
        if existing
        else ""
    )
    await message.answer(
        f"{prefix}Как прошёл ваш день?", reply_markup=rating_keyboard(today)
    )


@router.message(Command("week"))
async def cmd_week(message: Message) -> None:
    row = await db.get_user(message.from_user.id)
    if row is None or row["birth_date"] is None:
        await message.answer("Сначала укажите дату рождения — пришлите её сообщением.")
        return

    today = lifeweeks.local_today(row["timezone"])
    week = lifeweeks.life_week_number(row["birth_date"], today)
    total = lifeweeks.total_life_weeks()
    age = lifeweeks.age_in_years(row["birth_date"], today)
    await message.answer(
        f"Идёт <b>{week}-я неделя</b> вашей жизни.\n"
        f"Вам {age} лет, прожито {week} из ~{total} недель "
        f"({week * 100 // total}%).",
        reply_markup=webapp_keyboard(),
    )


@router.message(Command("stop"))
async def cmd_stop(message: Message) -> None:
    await db.update_settings(message.from_user.id, notifications=False)
    await message.answer(
        "Уведомления выключены. Включить обратно — /resume или в настройках приложения."
    )


@router.message(Command("resume"))
async def cmd_resume(message: Message) -> None:
    await db.update_settings(message.from_user.id, notifications=True)
    await message.answer("Уведомления снова включены.")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>LifeWeeks</b>\n\n"
        "/today — отметить сегодняшний день\n"
        "/week — какая идёт неделя жизни\n"
        "/stop — выключить уведомления\n"
        "/resume — включить обратно\n\n"
        "Дату рождения можно прислать сообщением: <code>31.12.1990</code>.",
        reply_markup=webapp_keyboard("🗓 Открыть LifeWeeks"),
    )


@router.message(F.text)
async def on_text(message: Message) -> None:
    """Свободный текст трактуем как попытку прислать дату рождения."""
    birth_date = parse_birth_date(message.text or "")
    if birth_date is None:
        await message.answer(
            "Не понял. Пришлите дату рождения в формате <code>31.12.1990</code> "
            "или посмотрите /help."
        )
        return

    user = message.from_user
    await db.upsert_user(
        user.id,
        username=user.username,
        first_name=user.first_name,
        language_code=user.language_code,
    )
    row = await db.set_birth_date(user.id, birth_date)
    today = lifeweeks.local_today(row["timezone"])
    week = lifeweeks.life_week_number(birth_date, today)
    await message.answer(
        f"Записал: <b>{birth_date.strftime('%d.%m.%Y')}</b>.\n"
        f"Сейчас идёт <b>{week}-я неделя</b> вашей жизни.",
        reply_markup=webapp_keyboard("🗓 Посмотреть сетку недель"),
    )


@router.callback_query(F.data.startswith("rate:"))
async def on_rate(callback: CallbackQuery) -> None:
    try:
        _, raw_day, rating = callback.data.split(":", 2)
        day = date.fromisoformat(raw_day)
    except ValueError:
        await callback.answer("Некорректная кнопка", show_alert=True)
        return
    if rating not in RATING_LABEL:
        await callback.answer("Некорректная оценка", show_alert=True)
        return

    row = await db.get_user(callback.from_user.id)
    if row is None:
        await callback.answer("Сначала напишите /start", show_alert=True)
        return

    await db.set_checkin(callback.from_user.id, day, rating, source="bot")
    await callback.answer(f"Записал: {RATING_LABEL[rating]}")

    text = (
        f"День {day.strftime('%d.%m')} отмечен: <b>{RATING_LABEL[rating]}</b>.\n"
        "Изменить — нажмите другую кнопку."
    )
    try:
        await callback.message.edit_text(text, reply_markup=rating_keyboard(day))
    except Exception:  # noqa: BLE001 — «message is not modified» и подобное не критично
        log.debug("не удалось отредактировать сообщение чек-ина", exc_info=True)


# --------------------------------------------------------------------------
# исходящие рассылки (вызываются планировщиком)
# --------------------------------------------------------------------------


async def _send(bot: Bot, chat_id: int, text: str, markup) -> bool:
    """Отправка с обработкой типовых отказов Telegram.

    Возвращает False, если отправку стоит повторить в следующий тик
    (флуд-контроль); при блокировке ботом — гасит уведомления и вернёт True,
    потому что повторять бессмысленно.
    """
    try:
        await bot.send_message(chat_id, text, reply_markup=markup)
        return True
    except TelegramRetryAfter as exc:
        log.warning("flood control для %s: retry after %s", chat_id, exc.retry_after)
        return False
    except TelegramForbiddenError:
        log.info("пользователь %s заблокировал бота — выключаю уведомления", chat_id)
        await db.update_settings(chat_id, notifications=False)
        return True
    except Exception:  # noqa: BLE001
        log.exception("не удалось отправить сообщение %s", chat_id)
        return False


async def send_daily_prompt(bot: Bot, user_row, day: date) -> bool:
    existing = await db.get_checkin(user_row["telegram_id"], day)
    if existing:
        # Пользователь уже отметился через Mini App — не дёргаем его повторно.
        return True
    return await _send(
        bot,
        user_row["telegram_id"],
        "Как прошёл ваш день?",
        rating_keyboard(day),
    )


async def send_weekly_report(bot: Bot, user_row, today: date) -> bool:
    birth_date = user_row["birth_date"]
    week_number = lifeweeks.life_week_number(birth_date, today)
    week_start = lifeweeks.previous_week_start(today)

    rows = await db.get_checkins(
        user_row["telegram_id"], week_start - timedelta(days=7), week_start + timedelta(days=6)
    )
    checkins = {r["day"]: r["rating"] for r in rows}
    report = lifeweeks.build_week_report(
        week_start=week_start,
        birth_date=birth_date,
        today=today,
        checkins=checkins,
        previous_checkins=checkins,
    )
    counts = report.counts

    lines = [
        f"Пошла <b>{week_number}-я неделя</b> вашей жизни.",
        "",
        f"Прошлая неделя ({week_start.strftime('%d.%m')}–"
        f"{(week_start + timedelta(days=6)).strftime('%d.%m')}):",
        f"🙂 {counts['good']}   😐 {counts['neutral']}   🙁 {counts['bad']}",
    ]
    if counts["skipped"]:
        lines.append(f"без оценки: {counts['skipped']}")
    if report.score_delta is not None:
        arrow = "↑" if report.score_delta > 0 else ("↓" if report.score_delta < 0 else "→")
        lines.append(f"Настроение к позапрошлой неделе: {arrow}")
    if report.rated_days == 0:
        lines.append("На прошлой неделе не было ни одной отметки — начнём заново?")

    return await _send(
        bot,
        user_row["telegram_id"],
        "\n".join(lines),
        webapp_keyboard("📊 Открыть отчёт"),
    )


def build_bot() -> Bot:
    settings = get_settings()
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp
