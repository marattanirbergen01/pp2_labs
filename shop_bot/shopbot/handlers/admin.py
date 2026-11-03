"""Продавец: импорт постов пересылкой, исправление разбора, «продано», статистика."""

from aiogram import F, Router
from aiogram.filters import Command, Filter as BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, TelegramObject

from ..catalog import Catalog, is_post_like
from ..categories import CATEGORY_LABELS, GENDERS
from ..config import Config
from ..db import Database
from ..keyboards import (
    Adm, button, category_choice_markup, describe, gender_choice_markup, markup, product_card,
    product_card_markup,
)
from ..parser import parse_sizes

router = Router(name="admin")


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject, config: Config) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and user.id in config.admin_ids)


router.message.filter(F.chat.type == "private", IsAdmin())
router.callback_query.filter(IsAdmin())


class EditSizes(StatesGroup):
    waiting = State()


HELP = (
    "<b>Как добавить товары</b>\n"
    "• <b>Новые посты</b> — добавьте бота администратором канала. Каждый новый пост он разберёт сам.\n"
    "• <b>Старые посты</b> — выделите посты в канале и перешлите их сюда (можно до 100 за раз).\n"
    "• <b>Продано</b> — допишите в пост слово «продано» или перешлите пост сюда и нажмите «❌ Продано».\n"
)


@router.message(Command("admin"))
async def admin_panel(message: Message, db: Database) -> None:
    stats = await db.stats()
    incomplete = len(await db.incomplete_products())
    text = (
        f"<b>Панель продавца</b>\n\n"
        f"🛍 В продаже: {stats['active']}\n❌ Продано: {stats['sold']}\n"
        f"❓ Требуют проверки: {incomplete}\n\n"
        f"👥 Покупателей: {stats['users']}\n🔎 Поисков: {stats['searches']}\n"
        f"🔔 Подписок на новинки: {stats['subscriptions']}\n"
    )
    demand = await db.unmet_demand()
    if demand:
        text += "\n<b>Искали, но не нашли:</b>\n" + "\n".join(f"• {describe(f)} — {n} раз" for f, n in demand)
    await message.answer(text + "\n\n" + HELP, reply_markup=markup(
        [button(f"Проверить нераспознанные ({incomplete})", Adm(act="next"))] if incomplete else []))


@router.message(EditSizes.waiting, F.text)
async def sizes_entered(message: Message, state: FSMContext, db: Database, catalog: Catalog) -> None:
    data = await state.get_data()
    await state.clear()
    product = await db.get_product(data["product_id"])
    sizes = parse_sizes(message.text, product.category)
    if not sizes:
        await message.answer("Не понял размеры 🤔 Пример: <code>46 48</code> или <code>S-L</code>. Нажмите «Размеры» ещё раз.")
        return
    await db.update_product(product.id, sizes=sizes, manual=True)
    product = await db.get_product(product.id)
    await message.answer(product_card(product), reply_markup=product_card_markup(product))
    await catalog.notify_subscribers(product)


@router.message(F.func(is_post_like), ~F.text.startswith("/"))
async def import_post(message: Message, catalog: Catalog) -> None:
    existing = await catalog.ingest(message, "import")
    if existing:
        # Пост уже в каталоге — показываем карточку (одну на альбом).
        catalog.debouncer.call(f"card:{message.chat.id}:{existing.id}",
                               lambda: catalog.send_card(message.chat.id, existing, "Этот товар уже в каталоге:"))


# --- карточка товара ---

async def refresh_card(call: CallbackQuery, db: Database, product_id: int) -> None:
    product = await db.get_product(product_id)
    await call.message.edit_text(product_card(product), reply_markup=product_card_markup(product))


@router.callback_query(Adm.filter(F.act == "next"))
async def next_incomplete(call: CallbackQuery, db: Database, catalog: Catalog) -> None:
    await call.answer()
    products = await db.incomplete_products()
    if not products:
        await call.message.answer("🎉 Все товары распознаны!")
        return
    await catalog.send_card(call.message.chat.id, products[0], f"Осталось проверить: {len(products)}")


@router.callback_query(Adm.filter(F.act == "card"))
async def card(call: CallbackQuery, callback_data: Adm, db: Database) -> None:
    await call.answer()
    await refresh_card(call, db, callback_data.id)


@router.callback_query(Adm.filter(F.act == "g"))
async def choose_gender(call: CallbackQuery, callback_data: Adm) -> None:
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=gender_choice_markup(callback_data.id))


@router.callback_query(Adm.filter(F.act == "c"))
async def choose_category(call: CallbackQuery, callback_data: Adm) -> None:
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=category_choice_markup(callback_data.id))


@router.callback_query(Adm.filter(F.act == "s"))
async def ask_sizes(call: CallbackQuery, callback_data: Adm, state: FSMContext) -> None:
    await call.answer()
    await state.set_state(EditSizes.waiting)
    await state.update_data(product_id=callback_data.id)
    await call.message.answer(f"Напишите размеры товара #{callback_data.id}, например: <code>46 48</code>, "
                              "<code>S-L</code>, <code>W32</code> или <code>one size</code>")


@router.callback_query(Adm.filter(F.act.in_({"setg", "setc"})))
async def set_field(call: CallbackQuery, callback_data: Adm, db: Database, catalog: Catalog) -> None:
    if callback_data.act == "setg" and callback_data.v in GENDERS:
        await db.update_product(callback_data.id, gender=callback_data.v, manual=True)
    elif callback_data.act == "setc" and callback_data.v in CATEGORY_LABELS:
        await db.update_product(callback_data.id, category=callback_data.v, manual=True)
    await call.answer("Сохранено")
    await refresh_card(call, db, callback_data.id)
    await catalog.notify_subscribers(await db.get_product(callback_data.id))


@router.callback_query(Adm.filter(F.act == "status"))
async def set_status(call: CallbackQuery, callback_data: Adm, db: Database) -> None:
    if callback_data.v in {"active", "sold", "deleted"}:
        await db.update_product(callback_data.id, status=callback_data.v)
    await call.answer("Сохранено")
    await refresh_card(call, db, callback_data.id)
