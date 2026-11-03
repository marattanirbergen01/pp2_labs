from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    bot_token: str
    admin_ids: set[int] = field(default_factory=set)
    channel_ids: set[int] = field(default_factory=set)  # пусто = любой канал, где бот админ
    db_path: str = "shop.db"
    default_gender: str | None = None                   # women / men, если в посте не указан пол
    page_size: int = 5
    album_delay: float = 1.5                            # сек ожидания остальных фото альбома
    send_delay: float = 1.0                             # сек между постами в выдаче
    shop_name: str = "Магазин"


def _ids(value: str) -> set[int]:
    return {int(x) for x in value.replace(" ", "").split(",") if x}


def load_env_file(path: str = ".env") -> None:
    """Простой загрузчик .env, чтобы не тянуть лишнюю зависимость."""
    file = Path(path)
    if not file.exists():
        return
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_config() -> Config:
    load_env_file()
    token = os.environ.get("BOT_TOKEN", "")
    if not token:
        raise SystemExit("Укажите BOT_TOKEN в файле .env (см. .env.example)")
    return Config(
        bot_token=token,
        admin_ids=_ids(os.environ.get("ADMIN_IDS", "")),
        channel_ids=_ids(os.environ.get("CHANNEL_IDS", "")),
        db_path=os.environ.get("DB_PATH", "shop.db"),
        default_gender=os.environ.get("DEFAULT_GENDER") or None,
        page_size=int(os.environ.get("PAGE_SIZE", "5")),
        send_delay=float(os.environ.get("SEND_DELAY", "1")),
        shop_name=os.environ.get("SHOP_NAME", "Магазин"),
    )
