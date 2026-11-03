"""Сценарии целиком: посты канала → поиск кнопками → выдача → подписка → «продано» → импорт."""

from __future__ import annotations

from datetime import datetime

import pytest
from aiogram.client.session.base import BaseSession
from aiogram.types import (
    CallbackQuery, Chat, Message, MessageId, MessageOriginChannel, PhotoSize, Update, User,
)

from shopbot.app import create_bot, create_dispatcher
from shopbot.catalog import Catalog
from shopbot.config import Config
from shopbot.db import Database
from shopbot.keyboards import Adm, Nav
from tests.test_parser import BLOUSE, CARDIGAN, CARGO, TSHIRT

CHANNEL = -1001
ADMIN = 100
BUYER = 555
NOW = datetime.now()
PHOTO = [PhotoSize(file_id="f", file_unique_id="u", width=1, height=1)]
_dispatcher = None  # роутеры aiogram подключаются один раз, поэтому диспетчер общий


class FakeSession(BaseSession):
    """Вместо Telegram записывает все запросы бота."""

    def __init__(self):
        super().__init__()
        self.calls = []

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        name = type(method).__name__
        if name == "SendMessage":
            return Message(message_id=5000 + len(self.calls), date=NOW,
                           chat=Chat(id=method.chat_id, type="private"), text=method.text)
        if name == "CopyMessages":
            return [MessageId(message_id=i) for i in method.message_ids]
        return True

    async def close(self):
        pass

    async def stream_content(self, *args, **kwargs):
        raise NotImplementedError

    def sent(self, method: str, chat_id: int | None = None):
        return [c for c in self.calls
                if type(c).__name__ == method and (chat_id is None or c.chat_id == chat_id)]

    def texts(self, chat_id: int) -> list[str]:
        return [c.text for c in self.sent("SendMessage", chat_id)]

    def buttons(self, call) -> list[str]:
        return [b.text for row in call.reply_markup.inline_keyboard for b in row]


@pytest.fixture
async def env():
    config = Config(bot_token="123:TEST", admin_ids={ADMIN}, default_gender="women", album_delay=0, send_delay=0)
    session = FakeSession()
    bot = create_bot(config, session=session)
    db = Database(":memory:")
    await db.connect()
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = create_dispatcher(bot, db, config)
    dp = _dispatcher
    dp["db"], dp["config"], dp["catalog"] = db, config, Catalog(bot, db, config)
    counter = iter(range(1, 10_000))

    async def feed(wait=True, **update):
        await dp.feed_update(bot, Update(update_id=next(counter), **update))
        if wait:
            await dp["catalog"].debouncer.wait()

    async def wait():
        await dp["catalog"].debouncer.wait()

    async def post(message_id, caption, media_group_id=None, edited=False, wait=True):
        msg = Message(message_id=message_id, date=NOW, chat=Chat(id=CHANNEL, type="channel"),
                      photo=PHOTO, caption=caption, media_group_id=media_group_id)
        await feed(wait=wait, **{"edited_channel_post" if edited else "channel_post": msg})

    async def private(user_id, text=None, **extra):
        msg = Message(message_id=next(counter), date=NOW, chat=Chat(id=user_id, type="private"),
                      from_user=User(id=user_id, is_bot=False, first_name="U"), text=text, **extra)
        await feed(message=msg)

    async def press(user_id, data):
        call = CallbackQuery(
            id=str(next(counter)), chat_instance="c", data=data.pack(),
            from_user=User(id=user_id, is_bot=False, first_name="U"),
            message=Message(message_id=4000, date=NOW, chat=Chat(id=user_id, type="private"), text="..."))
        await feed(callback_query=call)

    class Env:
        pass

    e = Env()
    e.session, e.db, e.post, e.private, e.press, e.feed, e.wait = session, db, post, private, press, feed, wait
    e.config, e.catalog = config, dp["catalog"]
    yield e
    await db.close()


async def test_channel_posts_are_parsed(env):
    await env.post(10, TSHIRT)
    await env.post(11, CARGO)
    products = await env.db.active_products()
    assert {(p.category, p.gender) for p in products} == {("tshirts", "women"), ("pants", "men")}


async def test_album_is_one_product(env):
    await env.post(20, CARDIGAN, media_group_id="g1")
    await env.post(21, None, media_group_id="g1")
    [product] = await env.db.active_products()
    assert product.message_ids == [20, 21]
    assert product.sizes == ["46", "48"]


async def test_buyer_search_flow(env):
    for i, text in enumerate([TSHIRT, CARDIGAN, BLOUSE, CARGO]):
        await env.post(30 + i, text)

    await env.private(BUYER, "/start")
    start = env.session.sent("SendMessage", BUYER)[-1]
    assert "Кого ищем?" in start.text
    assert any("Женское (3)" in b for b in env.session.buttons(start))

    await env.press(BUYER, Nav(step="c", g="w"))
    categories = env.session.sent("EditMessageText", BUYER)[-1]
    assert any("Футболки" in b for b in env.session.buttons(categories))

    await env.press(BUYER, Nav(step="s", g="w"))
    sizes = env.session.sent("EditMessageText", BUYER)[-1]
    assert [b for b in env.session.buttons(sizes) if b.startswith("48")] == ["48 (2)"]

    await env.press(BUYER, Nav(step="r", g="w", s="48"))
    copies = env.session.sent("CopyMessages", BUYER)
    assert [c.message_ids for c in copies] == [[31], [30]]  # новые сверху
    assert all(c.from_chat_id == CHANNEL for c in copies)
    assert "Это всё" in env.session.texts(BUYER)[-1]


async def test_more_button_pages(env):
    env_config_page = 5
    for i in range(7):
        await env.post(100 + i, f"{TSHIRT}\nАртикул {i}")
    await env.press(BUYER, Nav(step="r"))
    assert len(env.session.sent("CopyMessages", BUYER)) == env_config_page
    footer = env.session.sent("SendMessage", BUYER)[-1]
    assert "Показано 1–5 из 7" in footer.text and "▶️ Ещё" in env.session.buttons(footer)

    await env.press(BUYER, Nav(step="r", o=5))
    assert len(env.session.sent("CopyMessages", BUYER)) == 7
    assert "Это всё" in env.session.texts(BUYER)[-1]


async def test_subscription_gets_new_items(env):
    await env.press(BUYER, Nav(step="sub", g="w", s="48"))
    await env.post(40, BLOUSE)   # 54 — не подходит
    await env.post(41, TSHIRT)   # 46/48 — подходит
    copies = env.session.sent("CopyMessages", BUYER)
    assert [c.message_ids for c in copies] == [[41]]
    assert any("Новинка" in t for t in env.session.texts(BUYER))


async def test_sold_edit_hides_product(env):
    await env.post(50, TSHIRT)
    await env.post(50, TSHIRT + "\n❌ ПРОДАНО", edited=True)
    [product] = [p for p in [await env.db.get_product(1)]]
    assert product.status == "sold"
    assert await env.db.active_products() == []


async def test_admin_import_by_forwarding(env):
    origin = MessageOriginChannel(type="channel", date=NOW, chat=Chat(id=-100777, type="channel"), message_id=9)
    await env.private(ADMIN, None, photo=PHOTO, caption=CARDIGAN, forward_origin=origin)
    [product] = await env.db.active_products()
    assert product.chat_id == ADMIN and product.category == "hoodies"
    assert "Добавлено товаров: <b>1</b>" in env.session.texts(ADMIN)[-1]

    # Повторная пересылка не создаёт дубль, а показывает карточку.
    await env.private(ADMIN, None, photo=PHOTO, caption=CARDIGAN, forward_origin=origin)
    assert len(await env.db.active_products()) == 1
    assert "уже в каталоге" in env.session.texts(ADMIN)[-1]


async def test_unrecognized_post_goes_to_admin_and_can_be_fixed(env):
    await env.post(60, "Новинка 🔥\nЦена: 5 000 тг")
    assert "не всё удалось распознать" in env.session.texts(ADMIN)[-1]

    await env.press(ADMIN, Adm(act="setc", id=1, v="dresses"))
    product = await env.db.get_product(1)
    assert product.category == "dresses" and product.manual

    await env.press(ADMIN, Adm(act="status", id=1, v="sold"))
    assert (await env.db.get_product(1)).status == "sold"


async def test_buyer_cannot_use_admin_buttons(env):
    await env.post(60, "Новинка 🔥\nЦена: 5 000 тг")
    await env.press(BUYER, Adm(act="status", id=1, v="deleted"))
    assert (await env.db.get_product(1)).status == "active"


async def test_history_forwarded_into_channel_is_import(env):
    origin = MessageOriginChannel(type="channel", date=NOW, chat=Chat(id=-100777, type="channel"), message_id=5)
    msg = Message(message_id=70, date=NOW, chat=Chat(id=CHANNEL, type="channel"), photo=PHOTO,
                  caption="Новинка 🔥\nЦена: 5 000 тг", forward_origin=origin)
    await env.press(BUYER, Nav(step="sub"))  # подписан на всё
    await env.feed(channel_post=msg)
    assert env.session.sent("CopyMessages", BUYER) == []  # старые посты не рассылаются
    texts = env.session.texts(ADMIN)
    assert len(texts) == 1 and "Добавлено товаров: <b>1</b>" in texts[0]


async def test_admin_edits_sizes_by_text(env):
    await env.post(80, "Женское платье, новинка")
    await env.press(ADMIN, Adm(act="s", id=1))
    await env.private(ADMIN, "S-M")
    assert (await env.db.get_product(1)).sizes == ["44", "46"]


async def test_album_parts_arriving_concurrently_make_one_product(env):
    """Telegram присылает части альбома почти одновременно, бот обрабатывает их параллельно."""
    import asyncio
    await asyncio.gather(
        env.post(90, None, media_group_id="g9", wait=False),
        env.post(91, TSHIRT, media_group_id="g9", wait=False),
        env.post(92, None, media_group_id="g9", wait=False),
    )
    await env.wait()
    [product] = await env.db.active_products()
    assert product.message_ids == [90, 91, 92]
    assert product.category == "tshirts"


async def test_greeting_post_is_not_a_product(env):
    await env.post(95, "🌸 Девочки, всем доброе утро! ☀️\n\nЖелаем вам прекрасного дня и удачных покупок!")
    assert await env.db.active_products() == []
    assert env.session.texts(ADMIN) == []  # продавца не дёргаем


async def test_size_buttons_go_straight_to_results(env):
    await env.post(110, TSHIRT)
    await env.press(BUYER, Nav(step="s", g="w"))
    sizes = env.session.sent("EditMessageText", BUYER)[-1]
    steps = {Nav.unpack(b.callback_data).step for row in sizes.reply_markup.inline_keyboard for b in row
             if not b.text.startswith("⬅️")}
    assert steps == {"r"}  # шага «Цена» больше нет


async def test_posts_are_sent_one_per_delay(env, monkeypatch):
    import shopbot.catalog as catalog_module
    pauses = []

    async def fake_sleep(seconds):
        pauses.append(seconds)

    for i in range(3):
        await env.post(120 + i, f"{TSHIRT}\nАртикул {i}")
    env.config.send_delay = 1.0
    monkeypatch.setattr(catalog_module.asyncio, "sleep", fake_sleep)
    await env.catalog.send_products(BUYER, await env.db.search(Nav(step="r").flt))
    assert pauses == [1.0, 1.0]  # между тремя постами — две паузы по секунде


async def test_reposted_item_is_shown_once(env):
    await env.post(130, CARGO)
    await env.post(131, TSHIRT)
    await env.post(132, CARGO + "\n")  # продавец выложил ту же вещь ещё раз
    await env.press(BUYER, Nav(step="r"))
    copies = [c.message_ids for c in env.session.sent("CopyMessages", BUYER)]
    assert copies == [[132], [131]]  # только свежая публикация


async def test_reposted_item_sold_on_any_copy_is_hidden(env):
    await env.post(140, CARGO)                         # 29.10
    await env.post(141, CARGO)                         # 31.10 — повтор
    await env.post(142, CARGO)                         # 01.11 — повтор
    await env.post(141, "‼️продано‼️\n\n" + CARGO, edited=True)  # продали по копии от 31.10
    await env.press(BUYER, Nav(step="r"))
    assert env.session.sent("CopyMessages", BUYER) == []
