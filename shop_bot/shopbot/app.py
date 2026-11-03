from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from .catalog import Catalog
from .config import Config
from .db import Database
from .handlers import admin, channel, customer


def create_bot(config: Config, **kwargs) -> Bot:
    return Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML), **kwargs)


def create_dispatcher(bot: Bot, db: Database, config: Config) -> Dispatcher:
    dp = Dispatcher()
    dp["db"] = db
    dp["config"] = config
    dp["catalog"] = Catalog(bot, db, config)
    # Порядок важен: сначала продавец (импорт, правки), потом общие обработчики покупателя.
    dp.include_routers(channel.router, admin.router, customer.router)
    return dp


async def run(config: Config) -> None:
    db = Database(config.db_path)
    await db.connect()
    bot = create_bot(config)
    dp = create_dispatcher(bot, db, config)
    await bot.set_my_commands([
        BotCommand(command="start", description="Найти вещи"),
        BotCommand(command="subs", description="Мои подписки на новинки"),
    ])
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close()
        await bot.session.close()
