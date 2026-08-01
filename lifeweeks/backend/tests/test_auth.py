"""Тесты проверки подписи Telegram initData.

Это единственное, что отделяет API от подделки чужого telegram_id, поэтому
проверяется и happy path, и каждый способ подписи не пройти.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import unittest
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BOT_TOKEN = "123456:TEST-TOKEN"
os.environ.setdefault("BOT_TOKEN", BOT_TOKEN)
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/lifeweeks_test")

from app.auth import verify_init_data  # noqa: E402
from app.config import get_settings  # noqa: E402


def make_init_data(
    *, user: dict | None = None, auth_date: int | None = None, token: str = BOT_TOKEN,
    extra: dict | None = None, break_hash: bool = False,
) -> str:
    payload = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAExampleQueryId",
        "user": json.dumps(
            user or {"id": 42, "first_name": "Пётр", "username": "petros"},
            separators=(",", ":"),
            ensure_ascii=False,
        ),
    }
    if extra:
        payload.update(extra)

    check_string = "\n".join(f"{k}={payload[k]}" for k in sorted(payload))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if break_hash:
        digest = "0" * 64
    return urlencode({**payload, "hash": digest})


class TestVerifyInitData(unittest.TestCase):
    def setUp(self):
        get_settings.cache_clear()
        os.environ["BOT_TOKEN"] = BOT_TOKEN
        os.environ["INIT_DATA_TTL"] = "86400"

    def test_valid_init_data(self):
        user = verify_init_data(make_init_data())
        self.assertEqual(user.telegram_id, 42)
        self.assertEqual(user.username, "petros")
        self.assertEqual(user.first_name, "Пётр")

    def test_unknown_extra_fields_are_signed_and_accepted(self):
        # Telegram добавляет поля со временем; они входят в контрольную строку.
        user = verify_init_data(make_init_data(extra={"chat_type": "private"}))
        self.assertEqual(user.telegram_id, 42)

    def test_signature_field_is_excluded_from_hmac(self):
        # `signature` — Ed25519-подпись для третьих сторон, в HMAC не входит.
        init_data = make_init_data() + "&signature=abc123"
        self.assertEqual(verify_init_data(init_data).telegram_id, 42)

    def test_tampered_user_id_rejected(self):
        init_data = make_init_data()
        tampered = init_data.replace("42", "999")
        with self.assertRaises(ValueError):
            verify_init_data(tampered)

    def test_wrong_token_rejected(self):
        with self.assertRaises(ValueError):
            verify_init_data(make_init_data(token="999:OTHER-BOT"))

    def test_broken_hash_rejected(self):
        with self.assertRaises(ValueError):
            verify_init_data(make_init_data(break_hash=True))

    def test_missing_hash_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            verify_init_data("auth_date=1&user=%7B%22id%22%3A1%7D")
        self.assertIn("hash", str(ctx.exception))

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            verify_init_data("")

    def test_expired_init_data_rejected(self):
        old = int(time.time()) - 90000  # > 86400
        with self.assertRaises(ValueError) as ctx:
            verify_init_data(make_init_data(auth_date=old))
        self.assertIn("просрочен", str(ctx.exception))

    def test_fresh_init_data_within_ttl(self):
        recent = int(time.time()) - 3600
        self.assertEqual(verify_init_data(make_init_data(auth_date=recent)).telegram_id, 42)


class TestAppWiring(unittest.TestCase):
    def test_all_contract_routes_registered(self):
        from app.main import create_app

        paths = {route.path for route in create_app().routes}
        for endpoint in (
            "/get-user", "/set-birthdate", "/rate-day", "/rate-week",
            "/week-report", "/checkins", "/life-weeks", "/settings", "/health",
        ):
            self.assertIn(endpoint, paths, f"нет маршрута {endpoint}")


if __name__ == "__main__":
    unittest.main()
