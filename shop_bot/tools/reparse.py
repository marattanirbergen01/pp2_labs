"""Заново разбирает все сохранённые посты (после обновления бота). Посты не пересылаются.

Запуск (бота можно не останавливать):
    python tools/reparse.py

Внимание: статус «продано» берётся из текста поста, поэтому отметки, сделанные
кнопкой «❌ Продано», будут сброшены, если в самом посте нет слова «продано».
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shopbot.config import load_env_file  # noqa: E402
from shopbot.db import Database  # noqa: E402
from shopbot.parser import parse_post  # noqa: E402


async def main() -> None:
    load_env_file()
    db = Database(os.environ.get("DB_PATH", "shop.db"))
    await db.connect()
    default_gender = os.environ.get("DEFAULT_GENDER") or None
    rows = await (await db.conn.execute("SELECT id FROM products WHERE status != 'deleted'")).fetchall()
    changed = 0
    for row in rows:
        product = await db.get_product(row["id"])
        parsed = parse_post(product.text, default_gender)
        fields = {"title": parsed.title, "price": parsed.price,
                  "status": "sold" if parsed.sold else "active"}
        if not product.manual:
            fields.update(gender=parsed.gender, category=parsed.category, sizes=parsed.sizes)
        before = (product.title, product.price, product.status, product.gender, product.category, product.sizes)
        await db.update_product(product.id, **fields)
        after = await db.get_product(product.id)
        if before != (after.title, after.price, after.status, after.gender, after.category, after.sizes):
            changed += 1
    stats = await db.stats()
    await db.close()
    print(f"Проверено товаров: {len(rows)}, изменилось: {changed}. "
          f"В продаже: {stats['active']}, продано: {stats['sold']}.")


if __name__ == "__main__":
    asyncio.run(main())
