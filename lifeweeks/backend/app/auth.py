"""Проверка подписи Telegram WebApp initData.

Mini App отдаёт бэкенду строку `Telegram.WebApp.initData`. Она подписана
HMAC-ключом, производным от токена бота, поэтому telegram_id из неё нельзя
подделать — в отличие от id, который фронт просто кладёт в тело запроса.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status

from .config import get_settings

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class TelegramUser:
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    language_code: str | None = None


def _secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def verify_init_data(init_data: str) -> TelegramUser:
    """Разбирает и валидирует initData. Бросает ValueError при любой проблеме."""
    settings = get_settings()

    if not init_data:
        raise ValueError("пустой initData")

    # parse_qsl без strict_parsing: Telegram может добавлять новые поля.
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("в initData нет hash")

    # signature — поле для сторонней проверки третьей стороной (Ed25519),
    # в контрольную строку HMAC оно не входит.
    pairs.pop("signature", None)

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    expected = hmac.new(
        _secret_key(settings.bot_token), data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        raise ValueError("подпись initData не совпала")

    auth_date = pairs.get("auth_date")
    if auth_date is None:
        raise ValueError("в initData нет auth_date")
    age = time.time() - int(auth_date)
    if age > settings.init_data_ttl:
        raise ValueError(f"initData просрочен ({int(age)}s)")

    raw_user = pairs.get("user")
    if not raw_user:
        raise ValueError("в initData нет user")
    user: dict[str, Any] = json.loads(raw_user)

    return TelegramUser(
        telegram_id=int(user["id"]),
        username=user.get("username"),
        first_name=user.get("first_name"),
        language_code=user.get("language_code"),
    )


async def current_user(
    x_telegram_init_data: str | None = Header(default=None),
    x_telegram_user_id: str | None = Header(default=None),
) -> TelegramUser:
    """FastAPI-зависимость: достаёт пользователя из подписанного initData.

    `X-Telegram-User-Id` принимается только при ALLOW_INSECURE_AUTH=true —
    это режим локальной отладки без Telegram-клиента.
    """
    settings = get_settings()

    if x_telegram_init_data:
        try:
            return verify_init_data(x_telegram_init_data)
        except ValueError as exc:
            log.warning("initData отклонён: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"invalid init data: {exc}",
            ) from exc

    if settings.allow_insecure_auth and x_telegram_user_id:
        log.warning("insecure auth: доверяем X-Telegram-User-Id=%s", x_telegram_user_id)
        return TelegramUser(telegram_id=int(x_telegram_user_id))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="missing X-Telegram-Init-Data",
    )
