"""Проверяет посты с одинаковым текстом: это повтор одной вещи или разные вещи?

Сравнивает видео/фото оригинальных постов в канале-источнике: при повторной
публикации Telegram использует тот же файл, а новая вещь — это новое видео.
Работает от вашего аккаунта (как forward_history.py), ничего не меняет.

Запуск:
    python tools/check_duplicates.py --source "Сток @Dinara"
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections import defaultdict
from pathlib import Path

from telethon import TelegramClient, utils

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from forward_history import find_chat  # noqa: E402
from shopbot.config import load_env_file  # noqa: E402
from shopbot.db import Database  # noqa: E402


def media_id(msg) -> str | None:
    if msg is None or msg.media is None:
        return None
    if getattr(msg.media, "document", None):
        return f"doc:{msg.media.document.id}"
    if getattr(msg.media, "photo", None):
        return f"photo:{msg.media.photo.id}"
    return None


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, help="канал магазина, откуда пересылали посты")
    args = parser.parse_args()

    load_env_file()
    db = Database(os.environ.get("DB_PATH", "shop.db"))
    await db.connect()

    # Товары в продаже с одинаковым текстом.
    groups = defaultdict(list)
    for product in await db.active_products():
        key = " ".join(product.text.lower().split())
        if key:
            groups[key].append(product)
    groups = {k: v for k, v in groups.items() if len(v) > 1}
    if not groups:
        print("Товаров с одинаковым текстом нет.")
        return

    async with TelegramClient("forwarder", int(os.environ["API_ID"]), os.environ["API_HASH"]) as client:
        source = await find_chat(client, args.source)
        source_id = utils.get_peer_id(source)

        same, different = 0, []
        for products in groups.values():
            # Номера оригинальных сообщений в канале-источнике.
            originals = {}
            for product in products:
                rows = await (await db.conn.execute(
                    "SELECT key FROM message_keys WHERE product_id = ?", (product.id,))).fetchall()
                ids = [int(r["key"].split(":")[1]) for r in rows if r["key"].startswith(f"{source_id}:")]
                if ids:
                    originals[product.id] = ids
            if len(originals) < 2:
                continue
            all_ids = [i for ids in originals.values() for i in ids]
            messages = {m.id: m for m in await client.get_messages(source, ids=all_ids) if m}
            media = {pid: {media_id(messages.get(i)) for i in ids} - {None} for pid, ids in originals.items()}
            sets = list(media.values())
            if all(s and s & sets[0] for s in sets[1:]):
                same += 1
            else:
                dates = [messages[ids[0]].date.strftime("%d.%m") for ids in originals.values() if ids[0] in messages]
                different.append((products[0].title, len(products), ", ".join(dates)))

    await db.close()
    print(f"Групп с одинаковым текстом: {len(groups)}")
    print(f"  Повтор той же вещи (то же видео): {same}")
    print(f"  Одинаковый текст, но РАЗНОЕ видео (возможно, разные вещи): {len(different)}")
    for title, count, dates in different:
        print(f"    • {title} — {count} поста, даты: {dates}")


if __name__ == "__main__":
    asyncio.run(main())
