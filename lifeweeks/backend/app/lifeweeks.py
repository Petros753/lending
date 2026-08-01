"""Доменная арифметика: недели жизни, календарные недели, агрегация отчётов.

Две разные сущности сознательно разведены:

* **Неделя жизни** — привязана к дате рождения. Неделя с индексом `i`
  покрывает дни `[birth + 7i, birth + 7i + 6]`. По ней строится сетка
  "вся жизнь в неделях" и фраза "пошла N-я неделя".
* **Календарная неделя** — понедельник–воскресенье. По ней строится
  еженедельный отчёт, потому что рассылка приходит утром в понедельник.

Границы у них не совпадают, и это нормально: сетка — про биографию,
отчёт — про прошедшие семь дней.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

RATINGS = ("good", "neutral", "bad")

# Ожидаемая продолжительность жизни в годах — размер сетки в Mini App.
LIFE_EXPECTANCY_YEARS = 90
WEEKS_PER_YEAR = 52


def safe_zone(name: str | None, fallback: str = "Europe/Moscow") -> ZoneInfo:
    try:
        return ZoneInfo(name or fallback)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(fallback)


def local_now(timezone: str | None) -> datetime:
    return datetime.now(safe_zone(timezone))


def local_today(timezone: str | None) -> date:
    return local_now(timezone).date()


# --------------------------------------------------------------------------
# недели жизни
# --------------------------------------------------------------------------


def life_week_index(birth_date: date, on: date) -> int:
    """0-based индекс недели жизни, в которую попадает дата `on`."""
    return (on - birth_date).days // 7


def life_week_number(birth_date: date, on: date) -> int:
    """1-based номер недели — то, что показывается пользователю."""
    return life_week_index(birth_date, on) + 1


def life_week_bounds(birth_date: date, index: int) -> tuple[date, date]:
    start = birth_date + timedelta(days=7 * index)
    return start, start + timedelta(days=6)


def total_life_weeks(years: int = LIFE_EXPECTANCY_YEARS) -> int:
    return years * WEEKS_PER_YEAR


def age_in_years(birth_date: date, on: date) -> int:
    years = on.year - birth_date.year
    if (on.month, on.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


# --------------------------------------------------------------------------
# календарные недели
# --------------------------------------------------------------------------


def week_start_of(day: date) -> date:
    """Понедельник недели, в которую попадает `day`."""
    return day - timedelta(days=day.weekday())


def previous_week_start(day: date) -> date:
    return week_start_of(day) - timedelta(days=7)


def week_days(week_start: date) -> list[date]:
    return [week_start + timedelta(days=i) for i in range(7)]


# --------------------------------------------------------------------------
# агрегация
# --------------------------------------------------------------------------


@dataclass
class DayEntry:
    date: str
    weekday: int  # 0 = понедельник
    rating: str | None  # good / neutral / bad / None
    status: str  # rated / skipped / future / unborn


@dataclass
class WeekReport:
    week_start: str
    week_end: str
    life_week: int | None
    days: list[DayEntry] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    rated_days: int = 0
    trackable_days: int = 0
    score: float | None = None
    previous_score: float | None = None
    score_delta: float | None = None
    best_day: str | None = None
    worst_day: str | None = None
    current_streak: int = 0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["days"] = [asdict(d) if not isinstance(d, dict) else d for d in self.days]
        return data


#: Числовой вес оценки — используется для «среднего настроения» недели.
SCORE = {"good": 1.0, "neutral": 0.5, "bad": 0.0}


def week_score(ratings: list[str]) -> float | None:
    """Средний балл 0..1 по оценённым дням. None, если оценок нет."""
    if not ratings:
        return None
    return round(sum(SCORE[r] for r in ratings) / len(ratings), 4)


def build_week_report(
    *,
    week_start: date,
    birth_date: date | None,
    today: date,
    checkins: dict[date, str],
    previous_checkins: dict[date, str] | None = None,
) -> WeekReport:
    """Собирает отчёт за календарную неделю, начинающуюся в `week_start`.

    Пропущенный день (в прошлом, но без чек-ина) становится отдельной
    категорией `skipped`, а не исчезает из статистики — иначе неделя с одной
    оценкой «хорошо» выглядела бы как идеальная.
    """
    days: list[DayEntry] = []
    counts = {"good": 0, "neutral": 0, "bad": 0, "skipped": 0}
    ratings: list[str] = []

    for day in week_days(week_start):
        rating = checkins.get(day)
        if birth_date is not None and day < birth_date:
            status = "unborn"
        elif day > today:
            status = "future"
        elif rating is None:
            status = "skipped"
            counts["skipped"] += 1
        else:
            status = "rated"
            counts[rating] += 1
            ratings.append(rating)
        days.append(
            DayEntry(
                date=day.isoformat(),
                weekday=day.weekday(),
                rating=rating,
                status=status,
            )
        )

    trackable = sum(1 for d in days if d.status in ("rated", "skipped"))
    score = week_score(ratings)

    prev_score = None
    if previous_checkins:
        prev_start = week_start - timedelta(days=7)
        prev_ratings = [
            previous_checkins[d] for d in week_days(prev_start) if d in previous_checkins
        ]
        prev_score = week_score(prev_ratings)

    delta = None
    if score is not None and prev_score is not None:
        delta = round(score - prev_score, 4)

    rated_entries = [d for d in days if d.status == "rated"]
    best = next((d.date for d in rated_entries if d.rating == "good"), None)
    worst = next((d.date for d in rated_entries if d.rating == "bad"), None)

    return WeekReport(
        week_start=week_start.isoformat(),
        week_end=(week_start + timedelta(days=6)).isoformat(),
        life_week=life_week_number(birth_date, week_start) if birth_date else None,
        days=days,
        counts=counts,
        rated_days=len(rated_entries),
        trackable_days=trackable,
        score=score,
        previous_score=prev_score,
        score_delta=delta,
        best_day=best,
        worst_day=worst,
        current_streak=current_streak(checkins, today),
    )


def current_streak(checkins: dict[date, str], today: date) -> int:
    """Сколько дней подряд заканчивая сегодня (или вчера) есть чек-ин.

    Сегодняшний день ещё может быть не отмечен — вечер не наступил, — поэтому
    отсчёт стартует со вчера, если за сегодня оценки нет.
    """
    cursor = today if today in checkins else today - timedelta(days=1)
    streak = 0
    while cursor in checkins:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def aggregate_life_weeks(
    birth_date: date, checkins: dict[date, str], today: date
) -> list[dict]:
    """Сводка по неделям жизни — для раскраски сетки в Mini App.

    Возвращает только недели, в которых есть хотя бы один чек-ин: сетка
    на 90 лет — это 4680 ячеек, и гонять их все по сети незачем.
    """
    buckets: dict[int, dict[str, int]] = {}
    for day, rating in checkins.items():
        if day < birth_date:
            continue
        index = life_week_index(birth_date, day)
        bucket = buckets.setdefault(index, {"good": 0, "neutral": 0, "bad": 0})
        bucket[rating] += 1

    result = []
    for index in sorted(buckets):
        counts = buckets[index]
        ratings = [r for r, n in counts.items() for _ in range(n)]
        start, end = life_week_bounds(birth_date, index)
        result.append(
            {
                "index": index,
                "number": index + 1,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "counts": counts,
                "score": week_score(ratings),
            }
        )
    return result
