"""Пересылает посты канала-источника за последние N дней в ваш тестовый канал.

Работает от имени ВАШЕГО аккаунта Telegram (вы должны быть подписаны на источник).
Если тестового канала нет — скрипт создаст его сам и добавит туда бота
(по BOT_TOKEN из .env) администратором. Бот разберёт пересланные посты.

Запуск:
    python tools/forward_history.py --source "Dinara" --days 30

--source / --target — часть названия канала, @username или ссылка t.me/...
При первом запуске Telegram спросит номер телефона и пришлёт код — введите их в терминале.
API_ID и API_HASH возьмите на https://my.telegram.org → API development tools
и пропишите в .env рядом с BOT_TOKEN.
"""

import argparse
import asyncio
import os
import sys
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import CreateChannelRequest, EditAdminRequest
from telethon.tl.types import ChatAdminRights

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shopbot.config import load_env_file  # noqa: E402

BATCH = 100  # Telegram пересылает до 100 сообщений за раз


async def find_chat(client: TelegramClient, query: str, required: bool = True):
    if query.startswith(("@", "http", "t.me")):
        return await client.get_entity(query)
    query_lower = query.lower()
    matches = [d.entity async for d in client.iter_dialogs() if query_lower in (d.name or "").lower()]
    if not matches:
        if not required:
            return None
        raise SystemExit(f"Не нашёл чат, в названии которого есть «{query}»")
    if len(matches) > 1:
        names = ", ".join(getattr(m, "title", "?") for m in matches)
        raise SystemExit(f"Под «{query}» подходит несколько чатов: {names}. Уточните название.")
    return matches[0]


def bot_username() -> str:
    token = os.environ.get("BOT_TOKEN", "")
    if not token:
        raise SystemExit("Укажите BOT_TOKEN в .env")
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getMe", timeout=15) as resp:
        return "@" + json.load(resp)["result"]["username"]


async def ensure_target(client: TelegramClient, title: str):
    """Находит тестовый канал или создаёт его, и делает бота администратором."""
    target = await find_chat(client, title, required=False)
    if target is None:
        result = await client(CreateChannelRequest(title=title, about="Тестовый каталог для бота", broadcast=True))
        target = result.chats[0]
        print(f"Создал канал «{title}»")
    bot = await client.get_entity(bot_username())
    try:
        await client(EditAdminRequest(
            channel=target, user_id=bot, rank="bot",
            admin_rights=ChatAdminRights(post_messages=True, edit_messages=True, delete_messages=True)))
        print(f"Бот {bot.username} — администратор канала «{title}»")
    except Exception as e:  # уже админ или нет прав — сообщаем и продолжаем
        print(f"Не удалось сделать бота админом автоматически ({e}). Добавьте его вручную в настройках канала.")
    return target


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, help="канал, откуда брать посты")
    parser.add_argument("--target", default="Каталог (тест)",
                        help="ваш канал, куда пересылать; если его нет — будет создан")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    load_env_file()
    api_id, api_hash = os.environ.get("API_ID"), os.environ.get("API_HASH")
    if not api_id or not api_hash:
        raise SystemExit("Укажите API_ID и API_HASH в .env (см. my.telegram.org)")

    async with TelegramClient("forwarder", int(api_id), api_hash) as client:
        source = await find_chat(client, args.source)
        target = await ensure_target(client, args.target)
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
