"""Точка входа: FastAPI + aiogram (long polling) + APScheduler в одном процессе.

Один процесс — один systemd unit, как у соседнего tradingbot.service.
Бот работает на long polling, а не на вебхуке: это не требует ни отдельного
location в nginx, ни синхронизации с обновлением сертификата.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .api import router
from .bot import build_bot, build_dispatcher
from .config import get_settings
from .scheduler import start_scheduler

log = logging.getLogger(__name__)


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    await db.init_pool()
    await db.run_migrations()

    bot = build_bot()
    dispatcher = build_dispatcher()
    app.state.bot = bot

    # drop_pending_updates: после простоя не отвечаем на протухшие нажатия.
    polling = asyncio.create_task(
        dispatcher.start_polling(bot, handle_signals=False, drop_pending_updates=True),
        name="aiogram-polling",
    )
    scheduler = start_scheduler(bot)
    log.info("lifeweeks up on %s:%s", settings.api_host, settings.api_port)

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        await dispatcher.stop_polling()
        polling.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await polling
        await bot.session.close()
        await db.close_pool()
        log.info("lifeweeks stopped")


def create_app() -> FastAPI:
    app = FastAPI(title="LifeWeeks API", version="1.0.0", lifespan=lifespan)

    # Mini App и API живут на одном домене, поэтому CORS нужен только для
    # локальной разработки фронта — в проде запросы same-origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://lifeweeks.pukikuki.ru", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Telegram-Init-Data", "X-Telegram-User-Id"],
    )
    app.include_router(router)
    return app


app = create_app()


def main() -> None:
    configure_logging()
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    main()
