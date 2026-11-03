"""Чинит и заново разбирает сохранённые посты (после обновления бота). Посты не пересылаются.

1. Склеивает альбомы, которые старая версия бота сохранила несколькими товарами.
2. Заново разбирает текст: категория, пол, размеры, цена, «продано», «не товар».

Запуск (бота лучше остановить на время работы):
    python tools/reparse.py

Внимание: статус «продано» берётся из текста поста, поэтому отметки, сделанные
кнопкой «❌ Продано», будут сброшены, если в самом посте нет слова «продано».
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shopbot.config import load_env_file  # noqa: E402
from shopbot.db import Database  # noqa: E402
from shopbot.parser import parse_post  # noqa: E402


async def merge_album_duplicates(db: Database) -> int:
    rows = await (await db.conn.execute(
        "SELECT chat_id, media_group_id FROM products WHERE media_group_id IS NOT NULL "
        "GROUP BY chat_id, media_group_id HAVING COUNT(*) > 1")).fetchall()
    removed = 0
    for row in rows:
        parts = await (await db.conn.execute(
            "SELECT * FROM products WHERE chat_id = ? AND media_group_id = ? ORDER BY id",
            (row["chat_id"], row["media_group_id"]))).fetchall()
        keeper, others = parts[0], parts[1:]
        ids = sorted({i for p in parts for i in json.loads(p["message_ids"])})
        text = next((p["text"] for p in parts if p["text"]), "")
        other_ids = [p["id"] for p in others]
        marks = ",".join("?" * len(other_ids))
        await db.conn.execute("UPDATE products SET message_ids = ?, text = ? WHERE id = ?",
                              (json.dumps(ids), text, keeper["id"]))
        await db.conn.execute(f"UPDATE message_keys SET product_id = ? WHERE product_id IN ({marks})",
                              (keeper["id"], *other_ids))
        await db.conn.execute(f"DELETE FROM products WHERE id IN ({marks})", other_ids)
        removed += len(other_ids)
    await db.conn.commit()
    return removed


async def main() -> None:
    load_env_file()
    db = Database(os.environ.get("DB_PATH", "shop.db"))
    await db.connect()
    default_gender = os.environ.get("DEFAULT_GENDER") or None

    merged = await merge_album_duplicates(db)

    rows = await (await db.conn.execute("SELECT id FROM products WHERE status != 'deleted'")).fetchall()
    changed = 0
    for row in rows:
        product = await db.get_product(row["id"])
        parsed = parse_post(product.text, default_gender)
        if parsed.sold:
            status = "sold"
        elif product.manual or parsed.looks_like_product:
            status = "active"
        else:
            status = "hidden"
        fields = {"title": parsed.title, "price": parsed.price, "status": status}
        if not product.manual:
            fields.update(gender=parsed.gender, category=parsed.category, sizes=parsed.sizes)
        before = (product.title, product.price, product.status, product.gender, product.category, product.sizes)
        await db.update_product(product.id, **fields)
        after = await db.get_product(product.id)
        if before != (after.title, after.price, after.status, after.gender, after.category, after.sizes):
            changed += 1

    stats = await db.stats()
    hidden = (await (await db.conn.execute("SELECT COUNT(*) FROM products WHERE status = 'hidden'")).fetchone())[0]
    no_category = len([p for p in await db.incomplete_products() if p.category is None])
    await db.close()
    print(f"Склеено дублей альбомов: {merged}")
    print(f"Проверено товаров: {len(rows)}, изменилось: {changed}")
    print(f"В продаже: {stats['active']}, продано: {stats['sold']}, не товар (приветствия и т.п.): {hidden}, "
          f"без категории: {no_category}")


if __name__ == "__main__":
    asyncio.run(main())
