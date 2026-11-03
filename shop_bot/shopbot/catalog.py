"""Приём постов, разбор, рассылка подписчикам и отправка постов покупателям."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import Message, MessageOriginChannel

from .config import Config
from .db import Database, Product
from .keyboards import Adm, button, describe, markup, product_card, product_card_markup
from .parser import parse_post

log = logging.getLogger(__name__)


class Debouncer:
    """Запускает действие через `delay` секунд после последнего вызова с тем же ключом.

    Нужен для альбомов: Telegram присылает каждое фото альбома отдельным сообщением.
    """

    def __init__(self, delay: float):
        self.delay = delay
        self._tasks: dict[str, asyncio.Task] = {}   # ещё ждут
        self._running: set[asyncio.Task] = set()     # уже выполняются

    def call(self, key: str, action: Callable[[], Awaitable[None]]) -> None:
        task = self._tasks.pop(key, None)
        if task:
            task.cancel()
        self._tasks[key] = asyncio.create_task(self._run(key, action))

    async def _run(self, key: str, action: Callable[[], Awaitable[None]]) -> None:
        try:
            await asyncio.sleep(self.delay)
        except asyncio.CancelledError:
            return
        task = self._tasks.pop(key, None)
        if task:
            self._running.add(task)
        try:
            await action()
        except Exception:
            log.exception("Ошибка при обработке %s", key)
        finally:
            self._running.discard(task)

    async def wait(self) -> None:
        """Дождаться всех отложенных действий (для тестов)."""
        while self._tasks or self._running:
            await asyncio.gather(*self._tasks.values(), *self._running, return_exceptions=True)


def origin_key(message: Message) -> str | None:
    origin = message.forward_origin
    if isinstance(origin, MessageOriginChannel):
        return f"{origin.chat.id}:{origin.message_id}"
    return None


def is_post_like(message: Message) -> bool:
    return bool(message.photo or message.video or message.animation or message.document
                or message.video_note or message.caption or message.text)


class Catalog:
    def __init__(self, bot: Bot, db: Database, config: Config):
        self.bot = bot
        self.db = db
        self.config = config
        self.debouncer = Debouncer(config.album_delay)
        # Части альбома приходят почти одновременно и обрабатываются параллельно:
        # без блокировки каждая создала бы свой товар.
        self._ingest_lock = asyncio.Lock()
        self._imported: dict[int, list[int]] = {}

    # --- приём постов ---

    async def ingest(self, message: Message, source: str) -> Product | None:
        """Сохраняет пост как товар. source: "channel" или "import" (пересылка админом в бот).

        Возвращает уже существующий товар, если этот пост был добавлен раньше.
        """
        async with self._ingest_lock:
            return await self._ingest(message, source)

    async def _ingest(self, message: Message, source: str) -> Product | None:
        origin = origin_key(message)
        if origin and (existing := await self.db.product_by_key(origin)):
            return existing

        text = message.caption or message.text or ""
        has_media = bool(message.photo or message.video or message.animation or message.document)
        chat_id = message.chat.id
        if message.media_group_id:
            product = await self.db.product_by_group(chat_id, message.media_group_id)
            if product:
                await self.db.add_message(product, message.message_id, text)
                product_id = product.id
            else:
                product_id = await self.db.create_product(chat_id, message.message_id, message.media_group_id, text)
        else:
            if not has_media and not parse_post(text).category:
                return None  # обычное текстовое сообщение, не товар
            product_id = await self.db.create_product(chat_id, message.message_id, None, text)

        await self.db.add_keys(product_id, [f"{chat_id}:{message.message_id}"] + ([origin] if origin else []))
        group = f"{chat_id}:{message.media_group_id or message.message_id}"
        self.debouncer.call(group, lambda: self._finalize(product_id, source, chat_id))
        return None

    async def _finalize(self, product_id: int, source: str, chat_id: int) -> None:
        product = await self.apply_parse(product_id)
        if source == "import":
            # Старые посты не рассылаем подписчикам как новинки.
            await self.db.update_product(product_id, notified=True)
            self._imported.setdefault(chat_id, []).append(product_id)
            self.debouncer.call(f"import:{chat_id}", lambda: self._import_summary(chat_id))
            return
        if product.status == "active" and not product.complete:
            await self.send_card_to_admins(product, "🆕 Новый пост: не всё удалось распознать, поправьте:")
        await self.notify_subscribers(product)

    async def apply_parse(self, product_id: int) -> Product:
        product = await self.db.get_product(product_id)
        parsed = parse_post(product.text, self.config.default_gender)
        fields = {"title": parsed.title, "price": parsed.price}
        if not product.manual:
            fields.update(gender=parsed.gender, category=parsed.category, sizes=parsed.sizes)
        if parsed.sold and product.status == "active":
            fields["status"] = "sold"
        elif not product.manual and product.status in ("active", "hidden"):
            # Приветствия, отзывы, объявления: ни категории, ни цены, ни размера — не товар.
            fields["status"] = "active" if parsed.looks_like_product else "hidden"
        await self.db.update_product(product_id, **fields)
        return await self.db.get_product(product_id)

    async def on_edit(self, message: Message) -> None:
        product = await self.db.product_by_key(f"{message.chat.id}:{message.message_id}")
        if not product:
            await self.ingest(message, "channel")
            return
        text = message.caption or message.text
        if text is not None:
            await self.db.update_product(product.id, text=text)
        product = await self.apply_parse(product.id)
        await self.notify_subscribers(product)

    async def _import_summary(self, chat_id: int) -> None:
        ids = self._imported.pop(chat_id, [])
        products = [p for p in [await self.db.get_product(i) for i in ids] if p]
        incomplete = [p for p in products if p.status == "active" and not p.complete]
        sold = [p for p in products if p.status == "sold"]
        hidden = [p for p in products if p.status == "hidden"]
        text = f"📥 Добавлено товаров: <b>{len(products) - len(hidden)}</b>\n"
        text += f"✅ Распознано полностью: {len(products) - len(incomplete) - len(sold) - len(hidden)}\n"
        if hidden:
            text += f"💬 Пропущено постов без товара (приветствия, отзывы): {len(hidden)}\n"
        if sold:
            text += f"❌ Помечены как проданные: {len(sold)}\n"
        if incomplete:
            text += f"❓ Нужно проверить: {len(incomplete)}"
        reply = markup([button("Проверить нераспознанные", Adm(act="next"))]) if incomplete else None
        # Пересылка в канал (chat_id < 0) — отчёт админам в личку.
        for recipient in ([chat_id] if chat_id > 0 else self.config.admin_ids):
            try:
                await self.bot.send_message(recipient, text, reply_markup=reply)
            except (TelegramBadRequest, TelegramForbiddenError) as e:
                log.warning("Не удалось отправить отчёт %s: %s", recipient, e)

    # --- отправка ---

    async def send_products(self, chat_id: int, products: list[Product]) -> int:
        """Копирует посты покупателю. Удалённые из канала посты помечает и пропускает."""
        sent = 0
        for i, product in enumerate(products):
            if i:
                await asyncio.sleep(self.config.send_delay)  # посты приходят по одному, а не пачкой
            try:
                await self.bot.copy_messages(chat_id, product.chat_id, product.message_ids)
                sent += 1
            except TelegramBadRequest as e:
                log.warning("Пост товара #%s недоступен: %s", product.id, e)
                await self.db.update_product(product.id, status="deleted")
        return sent

    async def send_card(self, chat_id: int, product: Product, intro: str = "") -> None:
        await self.send_products(chat_id, [product])
        await self.bot.send_message(chat_id, (intro + "\n\n" if intro else "") + product_card(product),
                                    reply_markup=product_card_markup(product))

    async def send_card_to_admins(self, product: Product, intro: str = "") -> None:
        for admin_id in self.config.admin_ids:
            try:
                await self.send_card(admin_id, product, intro)
            except (TelegramBadRequest, TelegramForbiddenError) as e:
                log.warning("Не удалось написать админу %s: %s", admin_id, e)

    async def notify_subscribers(self, product: Product) -> None:
        if product.notified or product.status != "active" or not product.category:
            return
        await self.db.update_product(product.id, notified=True)
        for sub in await self.db.subscriptions():
            if not sub.filter.matches(product):
                continue
            try:
                await self.bot.send_message(sub.user_id, f"🔔 Новинка по вашему запросу: {describe(sub.filter)}")
                await self.send_products(sub.user_id, [product])
            except (TelegramBadRequest, TelegramForbiddenError) as e:
                log.info("Подписчик %s недоступен: %s", sub.user_id, e)
            await asyncio.sleep(0.05)  # не упираться в лимиты Telegram
