"""Пересылает посты канала-источника за последние N дней в ваш тестовый канал.

Работает от имени ВАШЕГО аккаунта Telegram (вы должны быть подписаны на источник
и быть админом тестового канала). Бот в тестовом канале разберёт посты сам.

Запуск:
    python tools/forward_history.py --source "Dinara" --target "Тест каталог" --days 30

--source / --target — часть названия канала, @username или ссылка t.me/...
При первом запуске Telegram пришлёт код входа в приложение — введите его в терминал.
API_ID и API_HASH возьмите на https://my.telegram.org → API development tools
и пропишите в .env рядом с BOT_TOKEN.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import FloodWaitError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shopbot.config import load_env_file  # noqa: E402

BATCH = 100  # Telegram пересылает до 100 сообщений за раз


async def find_chat(client: TelegramClient, query: str):
    if query.startswith(("@", "http", "t.me")):
        return await client.get_entity(query)
    query_lower = query.lower()
    matches = [d.entity async for d in client.iter_dialogs() if query_lower in (d.name or "").lower()]
    if not matches:
        raise SystemExit(f"Не нашёл чат, в названии которого есть «{query}»")
    if len(matches) > 1:
        names = ", ".join(getattr(m, "title", "?") for m in matches)
        raise SystemExit(f"Под «{query}» подходит несколько чатов: {names}. Уточните название.")
    return matches[0]


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, help="канал, откуда брать посты")
    parser.add_argument("--target", required=True, help="ваш канал, куда пересылать (бот там админ)")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    load_env_file()
    api_id, api_hash = os.environ.get("API_ID"), os.environ.get("API_HASH")
    if not api_id or not api_hash:
        raise SystemExit("Укажите API_ID и API_HASH в .env (см. my.telegram.org)")

    async with TelegramClient("forwarder", int(api_id), api_hash) as client:
        source = await find_chat(client, args.source)
        target = await find_chat(client, args.target)
        since = datetime.now(timezone.utc) - timedelta(days=args.days)

        messages = []
        async for msg in client.iter_messages(source):
            if msg.date < since:
                break
            if msg.action is None:  # пропускаем служебные сообщения
                messages.append(msg)
        messages.reverse()  # от старых к новым, чтобы в канале был тот же порядок
        print(f"Нашёл постов за {args.days} дн.: {len(messages)} (с учётом фото альбомов)")

        # Не разрываем альбомы между пачками.
        batches, current = [], []
        for msg in messages:
            starts_new_album = not (current and msg.grouped_id and current[-1].grouped_id == msg.grouped_id)
            if len(current) >= BATCH - 10 and starts_new_album:
                batches.append(current)
                current = []
            current.append(msg)
        if current:
            batches.append(current)

        for i, batch in enumerate(batches, 1):
            while True:
                try:
                    await client.forward_messages(target, [m.id for m in batch], from_peer=source)
                    break
                except FloodWaitError as e:
                    print(f"Telegram просит подождать {e.seconds} сек…")
                    await asyncio.sleep(e.seconds + 1)
            print(f"Переслано пачек: {i}/{len(batches)}")
            await asyncio.sleep(3)
        print("Готово! Бот разберёт посты за пару секунд. Проверьте /admin в боте.")


if __name__ == "__main__":
    asyncio.run(main())
