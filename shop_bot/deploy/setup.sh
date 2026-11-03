#!/usr/bin/env bash
# Устанавливает бота на Linux-сервер (Ubuntu или Oracle Linux) и запускает его как службу:
# бот работает круглосуточно, сам перезапускается при сбое и после перезагрузки сервера.
#
# Запуск на сервере (повторный запуск обновляет бота до свежей версии ветки):
#   curl -fsSL https://raw.githubusercontent.com/marattanirbergen01/pp2_labs/claude/using-100-3hizqe/shop_bot/deploy/setup.sh | bash
# или, если репозиторий уже скачан:
#   bash ~/pp2_labs/shop_bot/deploy/setup.sh
#
# Файлы .env и shop.db в git не хранятся: скопируйте их с Mac в ~/pp2_labs/shop_bot/ (см. deploy/README.md).
set -euo pipefail

BRANCH="${BRANCH:-claude/using-100-3hizqe}"
REPO="${REPO:-https://github.com/marattanirbergen01/pp2_labs.git}"
APP_DIR="${APP_DIR:-$HOME/pp2_labs}"
BOT_DIR="$APP_DIR/shop_bot"
SERVICE="${SERVICE:-shopbot}"
RUN_AS="${USER:-$(id -un)}"

echo "==> Устанавливаю git, Python и sqlite"
if command -v apt-get >/dev/null; then
    sudo apt-get update -y
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git python3 python3-venv python3-pip sqlite3
elif command -v dnf >/dev/null; then
    sudo dnf install -y git python3 python3-pip sqlite
else
    echo "Не знаю, как ставить пакеты на этой системе. Нужна Ubuntu или Oracle Linux." >&2
    exit 1
fi

echo "==> Скачиваю код (ветка $BRANCH)"
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" fetch origin "$BRANCH"
    git -C "$APP_DIR" checkout "$BRANCH"
    git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
else
    git clone --branch "$BRANCH" "$REPO" "$APP_DIR"
fi

echo "==> Ставлю зависимости в $BOT_DIR/.venv"
python3 -m venv "$BOT_DIR/.venv"
"$BOT_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$BOT_DIR/.venv/bin/pip" install --quiet -r "$BOT_DIR/requirements.txt"

echo "==> Настраиваю службу $SERVICE"
sudo tee "/etc/systemd/system/$SERVICE.service" >/dev/null <<EOF
[Unit]
Description=Telegram shop catalog bot ($SERVICE)
After=network-online.target
Wants=network-online.target

[Service]
User=$RUN_AS
WorkingDirectory=$BOT_DIR
ExecStart=$BOT_DIR/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE" >/dev/null

if [ ! -f "$BOT_DIR/.env" ]; then
    echo
    echo "Готово, но бот ещё НЕ запущен: нет файла $BOT_DIR/.env."
    echo "Скопируйте .env (и shop.db) с Mac, затем выполните: sudo systemctl restart $SERVICE"
    exit 0
fi

sudo systemctl restart "$SERVICE"
sleep 3
echo
sudo systemctl --no-pager --lines=15 status "$SERVICE" || true
echo
echo "Бот запущен. Логи: journalctl -u $SERVICE -f   Перезапуск: sudo systemctl restart $SERVICE"
