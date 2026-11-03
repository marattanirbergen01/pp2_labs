"""Посты канала: бот должен быть администратором канала."""

from aiogram import Router
from aiogram.types import Message

from ..catalog import Catalog
from ..config import Config

router = Router(name="channel")


def allowed(message: Message, config: Config) -> bool:
    return not config.channel_ids or message.chat.id in config.channel_ids


@router.channel_post()
async def new_post(message: Message, catalog: Catalog, config: Config) -> None:
    if allowed(message, config):
        # Пересланные в канал посты — это перенос старого ассортимента: без рассылки подписчикам.
        await catalog.ingest(message, "import" if message.forward_origin else "channel")


@router.edited_channel_post()
async def edited_post(message: Message, catalog: Catalog, config: Config) -> None:
    if allowed(message, config):
        await catalog.on_edit(message)
