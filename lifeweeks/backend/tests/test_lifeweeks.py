"""Тесты доменной арифметики. Без БД и сети — запускаются где угодно:

    python -m unittest discover -s tests
"""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import lifeweeks as lw  # noqa: E402


class TestLifeWeekMath(unittest.TestCase):
    birth = date(1990, 12, 31)  # понедельник

    def test_first_day_is_week_one(self):
        self.assertEqual(lw.life_week_number(self.birth, self.birth), 1)

    def test_day_six_still_week_one(self):
        self.assertEqual(lw.life_week_number(self.birth, date(1991, 1, 6)), 1)

    def test_day_seven_starts_week_two(self):
        self.assertEqual(lw.life_week_number(self.birth, date(1991, 1, 7)), 2)

    def test_bounds_are_seven_days_inclusive(self):
        start, end = lw.life_week_bounds(self.birth, 0)
        self.assertEqual(start, date(1990, 12, 31))
        self.assertEqual(end, date(1991, 1, 6))
        self.assertEqual((end - start).days, 6)

    def test_bounds_align_with_index(self):
        for index in (0, 1, 52, 1000):
            start, _ = lw.life_week_bounds(self.birth, index)
            self.assertEqual(lw.life_week_index(self.birth, start), index)

    def test_age_before_and_after_birthday(self):
        self.assertEqual(lw.age_in_years(self.birth, date(2020, 12, 30)), 29)
        self.assertEqual(lw.age_in_years(self.birth, date(2020, 12, 31)), 30)

    def test_leap_day_birth_date(self):
        leap = date(2000, 2, 29)
        self.assertEqual(lw.age_in_years(leap, date(2021, 2, 28)), 20)
        self.assertEqual(lw.age_in_years(leap, date(2021, 3, 1)), 21)


class TestCalendarWeeks(unittest.TestCase):
    def test_week_start_is_monday(self):
        for day in (date(2026, 7, 27), date(2026, 7, 30), date(2026, 8, 2)):
            self.assertEqual(lw.week_start_of(day), date(2026, 7, 27))
            self.assertEqual(lw.week_start_of(day).weekday(), 0)

    def test_previous_week_start(self):
        self.assertEqual(lw.previous_week_start(date(2026, 8, 3)), date(2026, 7, 27))

    def test_week_days_count(self):
        days = lw.week_days(date(2026, 7, 27))
        self.assertEqual(len(days), 7)
        self.assertEqual(days[-1], date(2026, 8, 2))


class TestWeekReport(unittest.TestCase):
    week_start = date(2026, 7, 27)  # понедельник
    birth = date(1990, 12, 31)

    def _report(self, checkins, today=date(2026, 8, 3), **kwargs):
        return lw.build_week_report(
            week_start=self.week_start,
            birth_date=self.birth,
            today=today,
            checkins=checkins,
            **kwargs,
        )

    def test_full_week_counts(self):
        checkins = {
            date(2026, 7, 27): "good",
            date(2026, 7, 28): "good",
            date(2026, 7, 29): "neutral",
            date(2026, 7, 30): "bad",
            date(2026, 7, 31): "good",
            date(2026, 8, 1): "neutral",
            date(2026, 8, 2): "good",
        }
        report = self._report(checkins)
        self.assertEqual(report.counts, {"good": 4, "neutral": 2, "bad": 1, "skipped": 0})
        self.assertEqual(report.rated_days, 7)
        self.assertEqual(report.trackable_days, 7)
        self.assertEqual(len(report.days), 7)

    def test_missing_past_day_becomes_skipped(self):
        report = self._report({date(2026, 7, 27): "good"})
        self.assertEqual(report.counts["good"], 1)
        self.assertEqual(report.counts["skipped"], 6)
        self.assertEqual(report.rated_days, 1)

    def test_future_days_are_not_skipped(self):
        # Отчёт смотрим в среду — четверг..воскресенье ещё не наступили.
        report = self._report({date(2026, 7, 27): "good"}, today=date(2026, 7, 29))
        statuses = [d.status for d in report.days]
        self.assertEqual(statuses[0], "rated")
        self.assertEqual(statuses[1], "skipped")
        self.assertEqual(statuses[2], "skipped")
        self.assertEqual(statuses[3:], ["future"] * 4)
        self.assertEqual(report.counts["skipped"], 2)
        self.assertEqual(report.trackable_days, 3)

    def test_days_before_birth_are_unborn(self):
        report = lw.build_week_report(
            week_start=self.week_start,
            birth_date=date(2026, 7, 30),
            today=date(2026, 8, 3),
            checkins={},
        )
        statuses = [d.status for d in report.days]
        self.assertEqual(statuses[:3], ["unborn"] * 3)
        self.assertEqual(statuses[3:], ["skipped"] * 4)

    def test_score_bounds(self):
        all_good = {d: "good" for d in lw.week_days(self.week_start)}
        all_bad = {d: "bad" for d in lw.week_days(self.week_start)}
        self.assertEqual(self._report(all_good).score, 1.0)
        self.assertEqual(self._report(all_bad).score, 0.0)
        self.assertIsNone(self._report({}).score)

    def test_score_delta_against_previous_week(self):
        checkins = {d: "good" for d in lw.week_days(self.week_start)}
        checkins.update({d: "bad" for d in lw.week_days(date(2026, 7, 20))})
        report = self._report(checkins, previous_checkins=checkins)
        self.assertEqual(report.score, 1.0)
        self.assertEqual(report.previous_score, 0.0)
        self.assertEqual(report.score_delta, 1.0)

    def test_no_previous_data_leaves_delta_none(self):
        report = self._report({date(2026, 7, 27): "good"}, previous_checkins={})
        self.assertIsNone(report.previous_score)
        self.assertIsNone(report.score_delta)

    def test_life_week_matches_week_start(self):
        report = self._report({})
        self.assertEqual(report.life_week, lw.life_week_number(self.birth, self.week_start))


class TestStreak(unittest.TestCase):
    today = date(2026, 8, 3)

    def test_streak_counts_back_from_today(self):
        checkins = {
            date(2026, 8, 3): "good",
            date(2026, 8, 2): "bad",
            date(2026, 8, 1): "neutral",
        }
        self.assertEqual(lw.current_streak(checkins, self.today), 3)

    def test_streak_survives_unrated_today(self):
        # Вечер ещё не наступил — серия не должна обнуляться.
        checkins = {date(2026, 8, 2): "good", date(2026, 8, 1): "good"}
        self.assertEqual(lw.current_streak(checkins, self.today), 2)

    def test_streak_breaks_on_gap(self):
        checkins = {date(2026, 8, 3): "good", date(2026, 8, 1): "good"}
        self.assertEqual(lw.current_streak(checkins, self.today), 1)

    def test_empty_streak(self):
        self.assertEqual(lw.current_streak({}, self.today), 0)


class TestAggregateLifeWeeks(unittest.TestCase):
    birth = date(1990, 12, 31)

    def test_groups_by_birth_anchored_week(self):
        checkins = {
            date(1990, 12, 31): "good",   # неделя 0
            date(1991, 1, 6): "bad",      # неделя 0
            date(1991, 1, 7): "neutral",  # неделя 1
        }
        weeks = lw.aggregate_life_weeks(self.birth, checkins, date(1991, 1, 10))
        self.assertEqual([w["index"] for w in weeks], [0, 1])
        self.assertEqual(weeks[0]["counts"], {"good": 1, "neutral": 0, "bad": 1})
        self.assertEqual(weeks[0]["score"], 0.5)
        self.assertEqual(weeks[1]["counts"], {"good": 0, "neutral": 1, "bad": 0})

    def test_ignores_days_before_birth(self):
        weeks = lw.aggregate_life_weeks(
            self.birth, {date(1990, 1, 1): "good"}, date(1991, 1, 10)
        )
        self.assertEqual(weeks, [])

    def test_only_weeks_with_data_returned(self):
        weeks = lw.aggregate_life_weeks(self.birth, {}, date(2026, 8, 3))
        self.assertEqual(weeks, [])


class TestRatingNormalization(unittest.TestCase):
    def test_aliases(self):
        from app.schemas import normalize_rating

        for raw, expected in (
            ("🙂", "good"), ("😐", "neutral"), ("🙁", "bad"),
            ("GOOD", "good"), (" bad ", "bad"), ("нейтрально", "neutral"),
        ):
            self.assertEqual(normalize_rating(raw), expected)

    def test_unknown_rating_rejected(self):
        from app.schemas import normalize_rating

        with self.assertRaises(ValueError):
            normalize_rating("отлично")


class TestBirthDateParsing(unittest.TestCase):
    def test_formats(self):
        from app.bot import parse_birth_date

        for raw in ("31.12.1990", "31-12-1990", "31 12 1990", "1990-12-31"):
            self.assertEqual(parse_birth_date(raw), date(1990, 12, 31))

    def test_rejects_garbage_and_future(self):
        from app.bot import parse_birth_date

        self.assertIsNone(parse_birth_date("привет"))
        self.assertIsNone(parse_birth_date("31.02.1990"))
        self.assertIsNone(parse_birth_date("01.01.2999"))
        self.assertIsNone(parse_birth_date("01.01.1800"))


class TestScheduleWindow(unittest.TestCase):
    def test_due_window(self):
        from datetime import datetime, time, timedelta

        from app.scheduler import _is_due

        target = time(20, 0)
        grace = timedelta(hours=3)
        self.assertTrue(_is_due(datetime(2026, 8, 3, 20, 0), target, grace))
        self.assertTrue(_is_due(datetime(2026, 8, 3, 22, 59), target, grace))
        self.assertFalse(_is_due(datetime(2026, 8, 3, 19, 59), target, grace))
        self.assertFalse(_is_due(datetime(2026, 8, 3, 23, 30), target, grace))


if __name__ == "__main__":
    unittest.main()
