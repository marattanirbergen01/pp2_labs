"""Хранилище товаров, покупателей и подписок (SQLite)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import aiosqlite

from .parser import SOLD

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,            -- откуда копировать пост (канал или чат с админом)
    message_ids TEXT NOT NULL,           -- JSON-список id сообщений (альбом)
    media_group_id TEXT,
    text TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    gender TEXT,
    category TEXT,
    sizes TEXT NOT NULL DEFAULT '',      -- «46,48»
    price INTEGER,
    status TEXT NOT NULL DEFAULT 'active',  -- active | sold | deleted
    manual INTEGER NOT NULL DEFAULT 0,   -- поля правил админ, не перезаписывать разбором
    notified INTEGER NOT NULL DEFAULT 0, -- подписчики уже получили уведомление
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS products_group ON products(chat_id, media_group_id);
-- Ключ «chat:message» -> товар. Хранит и фактическое место поста, и оригинал пересланного.
CREATE TABLE IF NOT EXISTS message_keys (
    key TEXT PRIMARY KEY,
    product_id INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    gender TEXT NOT NULL,
    category TEXT NOT NULL,
    size TEXT NOT NULL,
    price_max INTEGER NOT NULL,
    UNIQUE(user_id, gender, category, size, price_max)
);
CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    gender TEXT NOT NULL,
    category TEXT NOT NULL,
    size TEXT NOT NULL,
    price_max INTEGER NOT NULL,
    results INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def same_item_key(text: str) -> str:
    """Текст поста без пометок «продано», эмодзи и пробелов — чтобы узнавать повторные публикации."""
    return " ".join(re.sub(r"[^\w]+", " ", SOLD.sub(" ", text.lower())).split())


@dataclass
class Product:
    id: int
    chat_id: int
    message_ids: list[int]
    media_group_id: str | None
    text: str
    title: str
    gender: str | None
    category: str | None
    sizes: list[str]
    price: int | None
    status: str
    manual: bool
    notified: bool

    @property
    def complete(self) -> bool:
        return self.category is not None and bool(self.sizes)


@dataclass
class Filter:
    """Фильтр покупателя. «-» / 0 означает «любой»."""
    g: str = "-"   # w | m | k | -
    c: str = "-"   # ключ категории
    s: str = "-"   # размер
    p: int = 0     # цена до

    def matches(self, product: Product) -> bool:
        genders = {"w": ("women", "unisex"), "m": ("men", "unisex"), "k": ("kids",)}
        if self.g != "-" and product.gender not in genders[self.g]:
            return False
        if self.c != "-" and product.category != self.c:
            return False
        if self.s != "-" and self.s not in product.sizes:
            return False
        if self.p and (product.price is None or product.price > self.p):
            return False
        return True


@dataclass
class Subscription:
    id: int
    user_id: int
    filter: Filter = field(default_factory=Filter)


def _product(row) -> Product:
    return Product(
        id=row["id"], chat_id=row["chat_id"], message_ids=json.loads(row["message_ids"]),
        media_group_id=row["media_group_id"], text=row["text"], title=row["title"],
        gender=row["gender"], category=row["category"],
        sizes=[s for s in row["sizes"].split(",") if s], price=row["price"],
        status=row["status"], manual=bool(row["manual"]), notified=bool(row["notified"]),
    )


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    # --- товары ---

    async def product_by_key(self, key: str) -> Product | None:
        row = await (await self.conn.execute(
            "SELECT p.* FROM products p JOIN message_keys k ON k.product_id = p.id WHERE k.key = ?",
            (key,))).fetchone()
        return _product(row) if row else None

    async def product_by_group(self, chat_id: int, media_group_id: str) -> Product | None:
        row = await (await self.conn.execute(
            "SELECT * FROM products WHERE chat_id = ? AND media_group_id = ?",
            (chat_id, media_group_id))).fetchone()
        return _product(row) if row else None

    async def get_product(self, product_id: int) -> Product | None:
        row = await (await self.conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,))).fetchone()
        return _product(row) if row else None

    async def create_product(self, chat_id: int, message_id: int, media_group_id: str | None,
                             text: str) -> int:
        cur = await self.conn.execute(
            "INSERT INTO products (chat_id, message_ids, media_group_id, text) VALUES (?, ?, ?, ?)",
            (chat_id, json.dumps([message_id]), media_group_id, text))
        await self.conn.commit()
        return cur.lastrowid

    async def add_message(self, product: Product, message_id: int, text: str) -> None:
        ids = sorted(set(product.message_ids) | {message_id})
        await self.conn.execute(
            "UPDATE products SET message_ids = ?, text = CASE WHEN ? != '' THEN ? ELSE text END "
            "WHERE id = ?", (json.dumps(ids), text, text, product.id))
        await self.conn.commit()

    async def add_keys(self, product_id: int, keys: list[str]) -> None:
        await self.conn.executemany(
            "INSERT OR IGNORE INTO message_keys (key, product_id) VALUES (?, ?)",
            [(k, product_id) for k in keys])
        await self.conn.commit()

    async def update_product(self, product_id: int, **fields) -> None:
        if "sizes" in fields:
            fields["sizes"] = ",".join(fields["sizes"])
        for flag in ("manual", "notified"):
            if flag in fields:
                fields[flag] = int(fields[flag])
        sets = ", ".join(f"{k} = ?" for k in fields)
        await self.conn.execute(f"UPDATE products SET {sets} WHERE id = ?", (*fields.values(), product_id))
        await self.conn.commit()

    async def active_products(self) -> list[Product]:
        rows = await (await self.conn.execute(
            "SELECT * FROM products WHERE status = 'active' ORDER BY id DESC")).fetchall()
        return [_product(r) for r in rows]

    async def incomplete_products(self) -> list[Product]:
        return [p for p in await self.active_products() if not p.complete]

    async def search(self, flt: Filter) -> list[Product]:
        """Новые сверху.

        Магазины заново выкладывают непроданные вещи с тем же текстом: показываем такую
        вещь один раз (свежую публикацию), а если любая из копий помечена «продано» —
        не показываем совсем.
        """
        rows = await (await self.conn.execute(
            "SELECT text FROM products WHERE status = 'sold'")).fetchall()
        sold = {same_item_key(r["text"]) for r in rows} - {""}
        result, seen = [], set()
        for p in await self.active_products():
            key = same_item_key(p.text)
            if key and (key in seen or key in sold):
                continue
            seen.add(key)
            if p.category and flt.matches(p):
                result.append(p)
        return result

    # --- покупатели и подписки ---

    async def add_user(self, user_id: int) -> None:
        await self.conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await self.conn.commit()

    async def add_subscription(self, user_id: int, flt: Filter) -> bool:
        cur = await self.conn.execute(
            "INSERT OR IGNORE INTO subscriptions (user_id, gender, category, size, price_max) "
            "VALUES (?, ?, ?, ?, ?)", (user_id, flt.g, flt.c, flt.s, flt.p))
        await self.conn.commit()
        return cur.rowcount > 0

    async def subscriptions(self, user_id: int | None = None) -> list[Subscription]:
        query, args = "SELECT * FROM subscriptions", ()
        if user_id is not None:
            query, args = query + " WHERE user_id = ?", (user_id,)
        rows = await (await self.conn.execute(query + " ORDER BY id", args)).fetchall()
        return [Subscription(r["id"], r["user_id"], Filter(r["gender"], r["category"], r["size"], r["price_max"]))
                for r in rows]

    async def delete_subscription(self, user_id: int, sub_id: int) -> None:
        await self.conn.execute("DELETE FROM subscriptions WHERE id = ? AND user_id = ?", (sub_id, user_id))
        await self.conn.commit()

    async def log_search(self, user_id: int, flt: Filter, results: int) -> None:
        await self.conn.execute(
            "INSERT INTO searches (user_id, gender, category, size, price_max, results) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, flt.g, flt.c, flt.s, flt.p, results))
        await self.conn.commit()

    async def stats(self) -> dict:
        async def one(query: str) -> int:
            return (await (await self.conn.execute(query)).fetchone())[0]
        return {
            "active": await one("SELECT COUNT(*) FROM products WHERE status = 'active'"),
            "sold": await one("SELECT COUNT(*) FROM products WHERE status = 'sold'"),
            "users": await one("SELECT COUNT(*) FROM users"),
            "subscriptions": await one("SELECT COUNT(*) FROM subscriptions"),
            "searches": await one("SELECT COUNT(*) FROM searches"),
        }

    async def unmet_demand(self, limit: int = 5) -> list[tuple[Filter, int]]:
        """Что чаще всего искали и не нашли."""
        rows = await (await self.conn.execute(
            "SELECT gender, category, size, price_max, COUNT(*) AS n FROM searches WHERE results = 0 "
            "GROUP BY gender, category, size, price_max ORDER BY n DESC LIMIT ?", (limit,))).fetchall()
        return [(Filter(r["gender"], r["category"], r["size"], r["price_max"]), r["n"]) for r in rows]
