from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .categories import CATEGORY_LABELS, GENDERS
from .db import Filter, Product

GENDER_CODES = {"w": "women", "m": "men", "k": "kids"}
STATUS_LABELS = {"active": "✅ в продаже", "sold": "❌ продано", "deleted": "🗑 убран", "hidden": "💬 не товар"}


class Nav(CallbackData, prefix="n"):
    """Шаг поиска покупателя: g (пол) → c (категория) → s (размер) → p (цена) → r (результаты)."""
    step: str
    g: str = "-"
    c: str = "-"
    s: str = "-"
    p: int = 0
    o: int = 0

    @classmethod
    def of(cls, step: str, flt: Filter, o: int = 0) -> "Nav":
        return cls(step=step, g=flt.g, c=flt.c, s=flt.s, p=flt.p, o=o)

    @property
    def flt(self) -> Filter:
        return Filter(self.g, self.c, self.s, self.p)


class Unsub(CallbackData, prefix="u"):
    id: int


class Adm(CallbackData, prefix="a"):
    act: str
    id: int = 0
    v: str = "-"


def button(text: str, data: CallbackData) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data.pack())


def rows(buttons: list[InlineKeyboardButton], width: int) -> list[list[InlineKeyboardButton]]:
    return [buttons[i:i + width] for i in range(0, len(buttons), width)]


def markup(*button_rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[r for r in button_rows if r])


def money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₸"


def size_label(size: str) -> str:
    return "One size" if size == "ONE" else size


def describe(flt: Filter) -> str:
    parts = []
    if flt.g != "-":
        parts.append(GENDERS[GENDER_CODES[flt.g]])
    if flt.c != "-":
        parts.append(CATEGORY_LABELS.get(flt.c, flt.c))
    if flt.s != "-":
        parts.append(f"размер {size_label(flt.s)}")
    if flt.p:
        parts.append(f"до {money(flt.p)}")
    return " · ".join(parts) or "всё подряд"


def new_search_button() -> InlineKeyboardButton:
    return button("🔄 Новый поиск", Nav(step="g"))


# --- карточка товара для продавца ---

def product_card(product: Product) -> str:
    gender = GENDERS.get(product.gender or "", "❓ не определён")
    category = CATEGORY_LABELS.get(product.category or "", "❓ не определена")
    sizes = ", ".join(size_label(s) for s in product.sizes) or "❓ не определены"
    price = money(product.price) if product.price else "—"
    return (
        f"<b>Товар #{product.id}</b> {product.title and '«' + product.title + '»'}\n"
        f"Пол: {gender}\nКатегория: {category}\nРазмеры: {sizes}\nЦена: {price}\n"
        f"Статус: {STATUS_LABELS.get(product.status, product.status)}"
    )


def product_card_markup(product: Product) -> InlineKeyboardMarkup:
    pid = product.id
    status_button = (
        button("❌ Продано", Adm(act="status", id=pid, v="sold")) if product.status == "active"
        else button("↩️ Вернуть в продажу", Adm(act="status", id=pid, v="active"))
    )
    return markup(
        [button("Пол", Adm(act="g", id=pid)), button("Категория", Adm(act="c", id=pid)),
         button("Размеры", Adm(act="s", id=pid))],
        [status_button, button("🗑 Убрать", Adm(act="status", id=pid, v="deleted"))],
        [button("➡️ Следующий нераспознанный", Adm(act="next"))],
    )


def gender_choice_markup(product_id: int) -> InlineKeyboardMarkup:
    return markup(
        *rows([button(label, Adm(act="setg", id=product_id, v=key)) for key, label in GENDERS.items()], 2),
        [button("⬅️ Назад", Adm(act="card", id=product_id))],
    )


def category_choice_markup(product_id: int) -> InlineKeyboardMarkup:
    return markup(
        *rows([button(label, Adm(act="setc", id=product_id, v=key)) for key, label in CATEGORY_LABELS.items()], 2),
        [button("⬅️ Назад", Adm(act="card", id=product_id))],
    )
