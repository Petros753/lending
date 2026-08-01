"""Сквозные тесты API поверх настоящего Postgres.

Пропускаются, если не задан LIFEWEEKS_TEST_DSN — обычный `unittest discover`
на машине без базы остаётся зелёным.

    createdb lifeweeks_test
    LIFEWEEKS_TEST_DSN=postgresql://lifeweeks@127.0.0.1:5432/lifeweeks_test \\
        python -m unittest discover -s tests
"""

from __future__ import annotations

import asyncio
import os
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DSN = os.environ.get("LIFEWEEKS_TEST_DSN")

os.environ.setdefault("BOT_TOKEN", "123456:TEST-TOKEN")
os.environ.setdefault("DATABASE_URL", DSN or "postgresql://localhost/lifeweeks_test")

from tests.test_auth import BOT_TOKEN, make_init_data  # noqa: E402


@unittest.skipUnless(DSN, "нет LIFEWEEKS_TEST_DSN — сквозные тесты пропущены")
class TestApiFlow(unittest.TestCase):
    """Полный путь пользователя: регистрация → дата рождения → чек-ины → отчёт."""

    @classmethod
    def setUpClass(cls):
        os.environ["BOT_TOKEN"] = BOT_TOKEN
        os.environ["DATABASE_URL"] = DSN
        os.environ["DEFAULT_TIMEZONE"] = "UTC"

        from app.config import get_settings

        get_settings.cache_clear()

        import httpx
        from fastapi import FastAPI

        from app import db
        from app.api import router

        cls.db = db
        # Пул asyncpg привязан к событийному циклу, поэтому приложение,
        # соединения с БД и прямые вызовы db.* живут в одном цикле —
        # ASGI-транспорт httpx вместо TestClient с отдельным потоком.
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)

        cls.await_(db.init_pool())
        cls.await_(cls._reset())
        cls.await_(db.run_migrations())

        # Приложение без lifespan: бот и планировщик в сквозном тесте не нужны.
        app = FastAPI()
        app.include_router(router)
        cls.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

    @classmethod
    def await_(cls, coro):
        """Гоняет корутину в общем цикле. Имя с подчёркиванием — `run`
        занято самим TestCase."""
        return cls.loop.run_until_complete(coro)

    @classmethod
    async def _reset(cls):
        async with cls.db.pool().acquire() as conn:
            await conn.execute(
                "DROP TABLE IF EXISTS notifications_log, daily_checkins, "
                "week_ratings, users CASCADE"
            )

    @classmethod
    def tearDownClass(cls):
        cls.await_(cls.client.aclose())
        cls.await_(cls.db.close_pool())
        cls.loop.close()

    # ---- helpers ---------------------------------------------------------

    def auth(self, telegram_id: int = 42, **kwargs):
        user = {"id": telegram_id, "first_name": "Пётр", "username": "petros"}
        return {"X-Telegram-Init-Data": make_init_data(user=user, **kwargs)}

    def post(self, endpoint: str, json=None, telegram_id: int = 42):
        return self.await_(
            self.client.post(
                endpoint, json=json or {}, headers=self.auth(telegram_id)
            )
        )

    def get(self, endpoint: str, params=None, telegram_id: int = 42):
        return self.await_(
            self.client.get(endpoint, params=params, headers=self.auth(telegram_id))
        )

    # ---- тесты -----------------------------------------------------------

    def test_01_unauthenticated_is_rejected(self):
        response = self.await_(self.client.post("/get-user", json={}))
        self.assertEqual(response.status_code, 401)

    def test_02_forged_init_data_is_rejected(self):
        response = self.await_(
            self.client.post(
                "/get-user",
                json={},
                headers={"X-Telegram-Init-Data": make_init_data(token="999:OTHER")},
            )
        )
        self.assertEqual(response.status_code, 401)

    def test_03_get_user_creates_profile(self):
        body = self.post("/get-user").json()
        self.assertEqual(body["telegram_id"], 42)
        self.assertIsNone(body["birth_date"])
        self.assertTrue(body["is_new"])
        self.assertEqual(body["first_name"], "Пётр")

        # Второй вызов — уже не новый пользователь.
        self.assertFalse(self.post("/get-user").json()["is_new"])

    def test_04_set_birthdate_computes_life_week(self):
        body = self.post("/set-birthdate", {"birth_date": "1990-12-31"}).json()
        self.assertEqual(body["birth_date"], "1990-12-31")
        expected = (date.fromisoformat(body["today"]) - date(1990, 12, 31)).days // 7 + 1
        self.assertEqual(body["life_week"], expected)
        self.assertEqual(body["total_weeks"], 90 * 52)

    def test_05_future_birthdate_rejected(self):
        future = (date.today() + timedelta(days=1)).isoformat()
        self.assertEqual(
            self.post("/set-birthdate", {"birth_date": future}).status_code, 422
        )

    def test_06_rate_day_persists_and_overwrites(self):
        today = date.today().isoformat()
        first = self.post("/rate-day", {"date": today, "rating": "good"}).json()
        self.assertEqual(first["rating"], "good")

        second = self.post("/rate-day", {"date": today, "rating": "bad"}).json()
        self.assertEqual(second["rating"], "bad")

        self.assertEqual(self.post("/get-user").json()["today_rating"], "bad")
        self.assertEqual(self.post("/get-user").json()["checkins_total"], 1)
        self.assertEqual(self.post("/get-user").json()["streak"], 1)

    def test_07_rate_day_accepts_emoji(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        body = self.post("/rate-day", {"date": yesterday, "rating": "🙂"}).json()
        self.assertEqual(body["rating"], "good")

    def test_08_future_day_rejected(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        response = self.post("/rate-day", {"date": tomorrow, "rating": "good"})
        self.assertEqual(response.status_code, 400)

    def test_09_streak_counts_consecutive_days(self):
        today = date.today()
        for offset in range(0, 4):
            self.post(
                "/rate-day",
                {"date": (today - timedelta(days=offset)).isoformat(), "rating": "good"},
            )
        body = self.post("/rate-day", {"date": today.isoformat(), "rating": "good"}).json()
        self.assertGreaterEqual(body["streak"], 4)
        # get-user отдаёт ту же серию, что и rate-day — фронт берёт её при старте.
        self.assertEqual(self.post("/get-user").json()["streak"], body["streak"])

    def test_10_week_report_shape(self):
        week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
        body = self.get("/week-report", {"week_start": week_start}).json()

        self.assertEqual(body["week_start"], week_start)
        self.assertEqual(len(body["days"]), 7)
        self.assertEqual(
            set(body["counts"]), {"good", "neutral", "bad", "skipped"}
        )
        self.assertIsNotNone(body["life_week"])
        # Каждый день недели описан ровно одним статусом.
        self.assertTrue(
            all(d["status"] in ("rated", "skipped", "future", "unborn")
                for d in body["days"])
        )

    def test_11_week_report_defaults_to_previous_week(self):
        body = self.get("/week-report").json()
        today = date.today()
        expected = (today - timedelta(days=today.weekday() + 7)).isoformat()
        self.assertEqual(body["week_start"], expected)

    def test_11b_week_report_accepts_week_start_in_post_body(self):
        # Старый apiRequest() шлёт всё телом — POST не должен молча
        # подставлять прошлую неделю вместо запрошенной.
        today = date.today()
        week_start = (today - timedelta(days=today.weekday() + 14)).isoformat()
        body = self.post("/week-report", {"week_start": week_start}).json()
        self.assertEqual(body["week_start"], week_start)

    def test_11c_week_report_rejects_broken_week_start(self):
        response = self.post("/week-report", {"week_start": "не-дата"})
        self.assertEqual(response.status_code, 400)

    def test_12_checkins_range(self):
        today = date.today()
        body = self.get(
            "/checkins",
            {"from": (today - timedelta(days=7)).isoformat(), "to": today.isoformat()},
        ).json()
        self.assertGreaterEqual(len(body["items"]), 4)
        self.assertTrue(all({"date", "rating"} == set(i) for i in body["items"]))

    def test_13_life_weeks_grid(self):
        body = self.get("/life-weeks").json()
        self.assertEqual(body["birth_date"], "1990-12-31")
        self.assertGreater(body["current_week"], 1800)
        self.assertTrue(body["weeks"])
        self.assertTrue(all(0.0 <= w["score"] <= 1.0 for w in body["weeks"]))

    def test_14_legacy_rate_week_still_works(self):
        week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
        body = self.post("/rate-week", {"week_start": week_start, "rating": "good"}).json()
        self.assertTrue(body["ok"])
        grid = self.get("/life-weeks").json()
        self.assertEqual(grid["week_ratings"][-1]["rating"], "good")

    def test_15_settings_roundtrip(self):
        body = self.post(
            "/settings",
            {"timezone": "Asia/Bangkok", "daily_time": "21:30", "notifications": False},
        ).json()
        self.assertEqual(body["timezone"], "Asia/Bangkok")
        self.assertEqual(body["daily_time"], "21:30:00")
        self.assertFalse(body["notifications"])
        self.post("/settings", {"timezone": "UTC", "notifications": True})

    def test_16_invalid_timezone_rejected(self):
        response = self.post("/settings", {"timezone": "Mars/Olympus"})
        self.assertEqual(response.status_code, 400)

    def test_17_users_are_isolated(self):
        other = self.post("/get-user", telegram_id=777).json()
        self.assertIsNone(other["birth_date"])
        self.assertEqual(other["checkins_total"], 0)
        # Данные первого пользователя не протекли.
        self.assertEqual(self.post("/get-user").json()["birth_date"], "1990-12-31")

    def test_18_notification_claim_is_idempotent(self):
        async def scenario():
            today = date.today()
            first = await self.db.claim_notification(42, "daily", today)
            second = await self.db.claim_notification(42, "daily", today)
            await self.db.release_notification(42, "daily", today)
            third = await self.db.claim_notification(42, "daily", today)
            return first, second, third

        first, second, third = self.await_(scenario())
        self.assertTrue(first)
        self.assertFalse(second)   # повторная попытка в том же дне — отказ
        self.assertTrue(third)     # после release можно снова

    def test_19_rate_day_before_birth_rejected(self):
        response = self.post("/rate-day", {"date": "1980-01-01", "rating": "good"})
        self.assertEqual(response.status_code, 400)

    def test_20_health(self):
        self.assertEqual(self.get("/health").json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
