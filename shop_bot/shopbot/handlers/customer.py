"""Покупатель: поиск кнопками, выдача постов, подписки."""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from ..catalog import Catalog
from ..categories import CATEGORY_LABELS, CATEGORY_ORDER, GENDERS, PRICE_STEPS
from ..config import Config
from ..db import Database, Filter
from ..keyboards import (
    GENDER_CODES, Nav, Unsub, button, describe, markup, money, new_search_button, rows, size_label,
)
from ..parser import sort_sizes

router = Router(name="customer")
router.message.filter(F.chat.type == "private")

MAX_SUBSCRIPTIONS = 10


# --- шаги поиска ---

async def gender_options(db: Database, flt: Filter) -> list[tuple[str, int]]:
    options = []
    for code in GENDER_CODES:
        count = len(await db.search(Filter(g=code)))
        if count:
            options.append((code, count))
    return options


async def render(db: Database, nav: Nav) -> tuple[str, InlineKeyboardMarkup] | None:
    """Текст и кнопки для шага поиска. None — пора показывать результаты."""
    flt = nav.flt
    if nav.step == "g":
        options = await gender_options(db, flt)
        if len(options) > 1:
            buttons = [button(f"{GENDERS[GENDER_CODES[c]]} ({n})", Nav.of("c", Filter(g=c))) for c, n in options]
            buttons.append(button("Всё подряд", Nav.of("c", Filter())))
            return "Кого ищем?", markup(*rows(buttons, 2))
        if not options:
            return "Каталог пока пуст 🙈 Загляните чуть позже.", markup()
        nav = Nav.of("c", Filter(g=options[0][0]))
        flt = nav.flt
        return await _category_step(db, flt, back=False)
    if nav.step == "c":
        return await _category_step(db, flt, back=len(await gender_options(db, flt)) > 1)
    if nav.step == "s":
        result = await _size_step(db, flt)
        if result:
            return result
        nav = Nav.of("p", flt)
    if nav.step == "p":
        return await _price_step(db, nav.flt)
    return None


async def _category_step(db: Database, flt: Filter, back: bool):
    products = await db.search(Filter(g=flt.g))
    counts: dict[str, int] = {}
    for p in products:
        counts[p.category] = counts.get(p.category, 0) + 1
    buttons = [
        button(f"{CATEGORY_LABELS.get(c, c)} ({n})", Nav.of("s", Filter(g=flt.g, c=c)))
        for c, n in sorted(counts.items(), key=lambda kv: CATEGORY_ORDER.get(kv[0], 99))
    ]
    buttons.append(button(f"Все категории ({len(products)})", Nav.of("s", Filter(g=flt.g))))
    nav_row = [button("⬅️ Назад", Nav(step="g"))] if back else []
    return f"{describe(Filter(g=flt.g))}\nЧто ищем?", markup(*rows(buttons, 2), nav_row)


async def _size_step(db: Database, flt: Filter):
    products = await db.search(Filter(g=flt.g, c=flt.c))
    counts: dict[str, int] = {}
    for p in products:
        for s in p.sizes:
            counts[s] = counts.get(s, 0) + 1
    if not counts:
        return None
    base = Filter(g=flt.g, c=flt.c)
    buttons = [button(f"{size_label(s)} ({counts[s]})", Nav.of("p", Filter(flt.g, flt.c, s))) for s in sort_sizes(counts)]
    buttons.append(button("Любой размер", Nav.of("p", base)))
    return (f"{describe(base)}\nКакой размер?",
            markup(*rows(buttons, 4), [button("⬅️ Назад", Nav.of("c", Filter(g=flt.g)))]))


async def _price_step(db: Database, flt: Filter):
    products = await db.search(Filter(flt.g, flt.c, flt.s))
    prices = [p.price for p in products if p.price]
    steps = [(t, sum(1 for x in prices if x <= t)) for t in PRICE_STEPS]
    steps = [(t, n) for t, n in steps if 0 < n < len(products)]
    # убираем пороги, которые не меняют выдачу
    useful, last = [], -1
    for t, n in steps:
        if n != last:
            useful.append((t, n))
            last = n
    if not useful:
        return None
    base = Filter(flt.g, flt.c, flt.s)
    buttons = [button(f"до {money(t)} ({n})", Nav.of("r", Filter(flt.g, flt.c, flt.s, t))) for t, n in useful[:6]]
    buttons.append(button(f"Любая ({len(products)})", Nav.of("r", base)))
    back = Nav.of("s", Filter(flt.g, flt.c))
    return f"{describe(base)}\nЦена?", markup(*rows(buttons, 2), [button("⬅️ Назад", back)])


async def show_results(chat_id: int, user_id: int, flt: Filter, offset: int,
                       db: Database, catalog: Catalog, config: Config) -> None:
    bot = catalog.bot
    products = await db.search(flt)
    if offset == 0:
        await db.log_search(user_id, flt, len(products))
    if not products:
        await bot.send_message(
            chat_id, f"По запросу «{describe(flt)}» сейчас ничего нет 😔\n"
                     "Могу прислать, как только появится!",
            reply_markup=markup([button("🔔 Сообщить, когда появится", Nav.of("sub", flt))], [new_search_button()]))
        return
    if offset == 0:
        await bot.send_message(chat_id, f"Нашлось: <b>{len(products)}</b> 👇")
    page = products[offset:offset + config.page_size]
    await catalog.send_products(chat_id, page)
    end = offset + len(page)
    more = end < len(products)
    text = f"Показано {offset + 1}–{end} из {len(products)}" if more else "Это всё по вашему запросу 🙌"
    await bot.send_message(chat_id, text, reply_markup=markup(
        [button("▶️ Ещё", Nav.of("r", flt, end))] if more else [],
        [button("🔔 Сообщать о новинках", Nav.of("sub", flt))],
        [new_search_button()],
    ))


# --- обработчики ---

@router.message(CommandStart())
async def start(message: Message, db: Database, config: Config) -> None:
    await db.add_user(message.from_user.id)
    text, kb = await render(db, Nav(step="g"))
    hello = f"Привет! Это каталог <b>{config.shop_name}</b> 🛍\nПодберу вещи по размеру и цене — без листания ленты.\n\n"
    if message.from_user.id in config.admin_ids:
        hello += "<i>Вы продавец: /admin — панель управления.</i>\n\n"
    await message.answer(hello + text, reply_markup=kb)


@router.callback_query(Nav.filter(F.step == "sub"))
async def subscribe(call: CallbackQuery, callback_data: Nav, db: Database) -> None:
    flt = callback_data.flt
    if len(await db.subscriptions(call.from_user.id)) >= MAX_SUBSCRIPTIONS:
        await call.answer("Слишком много подписок. Удалите лишние: /subs", show_alert=True)
        return
    added = await db.add_subscription(call.from_user.id, flt)
    await call.answer("Готово! Пришлю, как появится 🔔" if added else "Вы уже подписаны на это", show_alert=True)


@router.callback_query(Nav.filter(F.step == "r"))
async def results(call: CallbackQuery, callback_data: Nav, db: Database, catalog: Catalog, config: Config) -> None:
    await call.answer()
    if callback_data.o == 0:
        await call.message.edit_text(f"🔎 {describe(callback_data.flt)}")
    else:
        await call.message.edit_reply_markup(reply_markup=None)
    await show_results(call.message.chat.id, call.from_user.id, callback_data.flt, callback_data.o,
                       db, catalog, config)


@router.callback_query(Nav.filter())
async def step(call: CallbackQuery, callback_data: Nav, db: Database, catalog: Catalog, config: Config) -> None:
    await call.answer()
    rendered = await render(db, callback_data)
    if rendered is None:  # для этого выбора нет размеров/цен — сразу результаты
        await call.message.edit_text(f"🔎 {describe(callback_data.flt)}")
        await show_results(call.message.chat.id, call.from_user.id, callback_data.flt, 0, db, catalog, config)
        return
    text, kb = rendered
    await call.message.edit_text(text, reply_markup=kb)


@router.message(Command("subs"))
async def list_subs(message: Message, db: Database) -> None:
    subs = await db.subscriptions(message.from_user.id)
    if not subs:
        await message.answer("У вас нет подписок. Найдите вещи через /start и нажмите «🔔 Сообщать о новинках».")
        return
    await message.answer(
        "Ваши подписки на новинки (нажмите, чтобы удалить):",
        reply_markup=markup(*[[button(f"❌ {describe(s.filter)}", Unsub(id=s.id))] for s in subs]))


@router.callback_query(Unsub.filter())
async def unsubscribe(call: CallbackQuery, callback_data: Unsub, db: Database) -> None:
    await db.delete_subscription(call.from_user.id, callback_data.id)
    await call.answer("Подписка удалена")
    subs = await db.subscriptions(call.from_user.id)
    await call.message.edit_reply_markup(
        reply_markup=markup(*[[button(f"❌ {describe(s.filter)}", Unsub(id=s.id))] for s in subs]))


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Я ищу вещи по кнопкам 🙂", reply_markup=markup([button("🔎 Начать поиск", Nav(step="g"))]))
