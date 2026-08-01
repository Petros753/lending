"""REST API для Telegram Mini App.

Контракт унаследован от старого n8n-вебхука: фронт ходит `POST /<endpoint>`
с JSON-телом. Поэтому у читающих ручек есть и GET-, и POST-вариант — GET
удобен для отладки curl-ом, POST совместим с уже написанным `apiRequest()`.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from . import db, lifeweeks
from .auth import TelegramUser, current_user
from .schemas import (
    BirthDateRequest,
    RateDayRequest,
    RateWeekRequest,
    SettingsRequest,
    UserResponse,
)

log = logging.getLogger(__name__)
router = APIRouter()


def _user_payload(row, *, today: date, today_rating: str | None, checkins_total: int,
                  streak: int = 0, is_new: bool = False) -> UserResponse:
    birth_date = row["birth_date"]
    return UserResponse(
        telegram_id=row["telegram_id"],
        birth_date=birth_date,
        username=row["username"],
        first_name=row["first_name"],
        timezone=row["timezone"],
        daily_time=row["daily_time"],
        weekly_time=row["weekly_time"],
        notifications=row["notifications"],
        today=today,
        life_week=lifeweeks.life_week_number(birth_date, today) if birth_date else None,
        total_weeks=lifeweeks.total_life_weeks() if birth_date else None,
        age=lifeweeks.age_in_years(birth_date, today) if birth_date else None,
        today_rating=today_rating,
        checkins_total=checkins_total,
        streak=streak,
        is_new=is_new,
    )


async def _user_stats(telegram_id: int, today: date) -> tuple[str | None, int, int]:
    """Оценка за сегодня, всего чек-инов и длина текущей серии.

    Серия считается по последним ~400 дням: длиннее непрерывная серия
    физически не бывает интереснее, а тянуть всю историю ради неё незачем.
    """
    rows = await db.recent_checkins(telegram_id, today - timedelta(days=400))
    checkins = {r["day"]: r["rating"] for r in rows}
    total = await db.count_checkins(telegram_id)
    return checkins.get(today), total, lifeweeks.current_streak(checkins, today)


async def _load_user_or_404(telegram_id: int):
    row = await db.get_user(telegram_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    return row


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.post("/get-user")
@router.get("/get-user")
async def get_user(user: TelegramUser = Depends(current_user)) -> UserResponse:
    """Возвращает профиль, создавая его при первом заходе.

    Это же основная точка регистрации: онбординг в Mini App вызывает
    get-user, видит `birth_date: null` и показывает экран ввода даты.
    """
    existed = await db.get_user(user.telegram_id)
    row = await db.upsert_user(
        user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        language_code=user.language_code,
    )
    today = lifeweeks.local_today(row["timezone"])
    today_rating, total, streak = await _user_stats(user.telegram_id, today)
    return _user_payload(
        row,
        today=today,
        today_rating=today_rating,
        checkins_total=total,
        streak=streak,
        is_new=existed is None,
    )


@router.post("/set-birthdate")
async def set_birthdate(
    payload: BirthDateRequest, user: TelegramUser = Depends(current_user)
) -> UserResponse:
    """Устанавливает или меняет дату рождения.

    История смены не ведётся намеренно: чек-ины хранятся по абсолютным датам,
    поэтому сетка недель и номер текущей недели пересчитываются из новой даты
    детерминированно, без миграции данных.
    """
    await db.upsert_user(
        user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        language_code=user.language_code,
    )
    row = await db.set_birth_date(user.telegram_id, payload.birth_date)
    today = lifeweeks.local_today(row["timezone"])
    today_rating, total, streak = await _user_stats(user.telegram_id, today)
    return _user_payload(
        row, today=today, today_rating=today_rating, checkins_total=total, streak=streak,
    )


@router.post("/rate-day")
async def rate_day(
    payload: RateDayRequest, user: TelegramUser = Depends(current_user)
) -> dict:
    """Ежедневный чек-ин из Mini App. Повторный вызов за тот же день перезаписывает."""
    row = await _load_user_or_404(user.telegram_id)
    today = lifeweeks.local_today(row["timezone"])
    day = payload.date or today

    if day > today:
        raise HTTPException(status_code=400, detail="нельзя оценить будущий день")
    if row["birth_date"] and day < row["birth_date"]:
        raise HTTPException(status_code=400, detail="день раньше даты рождения")

    saved = await db.set_checkin(user.telegram_id, day, payload.rating, source="webapp")
    _, total, streak = await _user_stats(user.telegram_id, today)
    return {
        "ok": True,
        "date": saved["day"].isoformat(),
        "rating": saved["rating"],
        "streak": streak,
        "checkins_total": total,
    }


@router.post("/rate-week")
async def rate_week(
    payload: RateWeekRequest, user: TelegramUser = Depends(current_user)
) -> dict:
    """Недельная оценка — сохраняется для совместимости со старым фронтом."""
    await _load_user_or_404(user.telegram_id)
    week_start = lifeweeks.week_start_of(payload.week_start)
    await db.set_week_rating(user.telegram_id, week_start, payload.rating)
    return {"ok": True, "week_start": week_start.isoformat(), "rating": payload.rating}


@router.post("/week-report")
@router.get("/week-report")
async def week_report(
    request: Request,
    week_start: date | None = Query(default=None),
    user: TelegramUser = Depends(current_user),
) -> dict:
    """Отчёт за календарную неделю. Без параметра — за прошедшую неделю.

    `week_start` принимается и в query, и в теле POST: старый `apiRequest()`
    во фронте всегда шлёт JSON-тело, и молча игнорировать его — значит
    отдавать не ту неделю, о которой просили.
    """
    row = await _load_user_or_404(user.telegram_id)
    today = lifeweeks.local_today(row["timezone"])

    if week_start is None and request.method == "POST":
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001 — пустое или не-JSON тело допустимо
            body = None
        raw = (body or {}).get("week_start") if isinstance(body, dict) else None
        if raw:
            try:
                week_start = date.fromisoformat(raw)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400, detail=f"некорректный week_start: {raw}"
                ) from exc

    start = (
        lifeweeks.week_start_of(week_start)
        if week_start
        else lifeweeks.previous_week_start(today)
    )

    # Берём две недели сразу: текущую для отчёта и предыдущую для дельты.
    rows = await db.get_checkins(
        user.telegram_id, start - timedelta(days=7), start + timedelta(days=6)
    )
    checkins = {r["day"]: r["rating"] for r in rows}

    report = lifeweeks.build_week_report(
        week_start=start,
        birth_date=row["birth_date"],
        today=today,
        checkins=checkins,
        previous_checkins=checkins,
    )
    payload = report.to_dict()
    payload["today"] = today.isoformat()
    payload["has_next"] = start + timedelta(days=7) <= lifeweeks.week_start_of(today)
    return payload


@router.post("/checkins")
@router.get("/checkins")
async def checkins(
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    user: TelegramUser = Depends(current_user),
) -> dict:
    """Плоский список чек-инов за период. По умолчанию — последние 90 дней."""
    row = await _load_user_or_404(user.telegram_id)
    today = lifeweeks.local_today(row["timezone"])
    end = date_to or today
    start = date_from or (end - timedelta(days=90))
    if start > end:
        raise HTTPException(status_code=400, detail="from позже to")

    rows = await db.get_checkins(user.telegram_id, start, end)
    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "items": [
            {"date": r["day"].isoformat(), "rating": r["rating"]} for r in rows
        ],
    }


@router.post("/life-weeks")
@router.get("/life-weeks")
async def life_weeks(user: TelegramUser = Depends(current_user)) -> dict:
    """Сводка по неделям жизни для раскраски сетки."""
    row = await _load_user_or_404(user.telegram_id)
    if row["birth_date"] is None:
        raise HTTPException(status_code=400, detail="birth_date не задан")

    today = lifeweeks.local_today(row["timezone"])
    rows = await db.get_checkins(user.telegram_id, row["birth_date"], today)
    checkins = {r["day"]: r["rating"] for r in rows}
    week_rows = await db.get_week_ratings(user.telegram_id)

    return {
        "birth_date": row["birth_date"].isoformat(),
        "today": today.isoformat(),
        "current_week": lifeweeks.life_week_number(row["birth_date"], today),
        "total_weeks": lifeweeks.total_life_weeks(),
        "weeks": lifeweeks.aggregate_life_weeks(row["birth_date"], checkins, today),
        "week_ratings": [
            {"week_start": r["week_start"].isoformat(), "rating": r["rating"]}
            for r in week_rows
        ],
    }


@router.post("/settings")
async def update_settings(
    payload: SettingsRequest, user: TelegramUser = Depends(current_user)
) -> UserResponse:
    """Таймзона, время рассылок, вкл/выкл уведомлений."""
    await _load_user_or_404(user.telegram_id)
    if payload.timezone is not None:
        # Некорректная зона молча схлопнулась бы в дефолт при рассылке —
        # лучше сказать об этом сразу.
        try:
            lifeweeks.ZoneInfo(payload.timezone)
        except Exception as exc:  # noqa: BLE001 — ZoneInfoNotFoundError/ValueError
            raise HTTPException(
                status_code=400, detail=f"неизвестная таймзона: {payload.timezone}"
            ) from exc

    row = await db.update_settings(
        user.telegram_id,
        timezone=payload.timezone,
        daily_time=payload.daily_time,
        weekly_time=payload.weekly_time,
        notifications=payload.notifications,
    )
    today = lifeweeks.local_today(row["timezone"])
    today_rating, total, streak = await _user_stats(user.telegram_id, today)
    return _user_payload(
        row, today=today, today_rating=today_rating, checkins_total=total, streak=streak,
    )
