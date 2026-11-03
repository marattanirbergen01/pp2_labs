# Запуск бота на бесплатном сервере Oracle Cloud

После этого бот работает круглосуточно, а Mac больше не нужен. Один сервер может держать
несколько ботов — для каждого своя папка и своя служба.

## 1. Регистрация (делаете сами, ≈15 минут)

1. Откройте [oracle.com/cloud/free](https://www.oracle.com/cloud/free/) → **Start for free**.
2. Почта, страна (Kazakhstan), телефон. Нужна банковская карта для проверки — по тарифу
   Always Free деньги не списываются, но условия проверьте на сайте сами.
3. **Home Region** выбирается один раз и навсегда. Берите ближайший, где есть свободные
   серверы (часто советуют Frankfurt или Amsterdam).

## 2. Ключ для входа на сервер (на Mac)

```bash
ssh-keygen -t ed25519 -f ~/.ssh/oracle_bot -N ""
cat ~/.ssh/oracle_bot.pub     # эту строку вставите в Oracle на шаге 3
```

## 3. Создание сервера (в консоли Oracle)

1. Меню → **Compute → Instances → Create instance**.
2. **Image:** Canonical **Ubuntu** (22.04 или 24.04).
3. **Shape:** бесплатный — `VM.Standard.E2.1.Micro` (AMD) или `VM.Standard.A1.Flex`
   (Ampere, 1 OCPU и 6 GB хватит с запасом). Ищите пометку **Always Free-eligible**.
   Если пишет «Out of capacity» — попробуйте другой shape или повторите позже.
4. **Add SSH keys → Paste public keys** — вставьте строку из шага 2.
5. **Create**. Через пару минут появится **Public IP address** — запишите его.

Открывать порты не нужно: бот сам ходит в Telegram, к нему никто не подключается.

## 4. Установка бота (на Mac, в Терминале)

```bash
IP=<Public IP из шага 3>
ssh -i ~/.ssh/oracle_bot ubuntu@$IP 'curl -fsSL https://raw.githubusercontent.com/marattanirbergen01/pp2_labs/claude/using-100-3hizqe/shop_bot/deploy/setup.sh | bash'
```

Скрипт поставит Python, скачает код и создаст службу `shopbot`.

## 5. Перенос настроек и базы

**Сначала остановите бота на Mac** (`Ctrl+C` в его окне): если один и тот же бот запущен
в двух местах, Telegram отвечает ошибкой `Conflict`.

```bash
cd ~/pp2_labs/shop_bot
scp -i ~/.ssh/oracle_bot .env shop.db ubuntu@$IP:~/pp2_labs/shop_bot/
ssh -i ~/.ssh/oracle_bot ubuntu@$IP 'sudo systemctl restart shopbot && journalctl -u shopbot -n 20 --no-pager'
```

Файлы `.env` (токен!) и `shop.db` передаются только напрямую на сервер, в git их класть нельзя.

## Дальше

| Что | Команда (на Mac) |
|---|---|
| Логи вживую | `ssh -i ~/.ssh/oracle_bot ubuntu@$IP 'journalctl -u shopbot -f'` |
| Обновить бота до свежей версии | повторить команду из шага 4 |
| Перезапустить | `ssh -i ~/.ssh/oracle_bot ubuntu@$IP 'sudo systemctl restart shopbot'` |
| Остановить | `ssh -i ~/.ssh/oracle_bot ubuntu@$IP 'sudo systemctl stop shopbot'` |
| Скачать базу на Mac | `scp -i ~/.ssh/oracle_bot ubuntu@$IP:~/pp2_labs/shop_bot/shop.db ./shop.db` |

Скрипты из `tools/` (`reparse.py`, `forward_history.py`) запускайте на сервере:
`ssh -i ~/.ssh/oracle_bot ubuntu@$IP`, затем `cd ~/pp2_labs/shop_bot && .venv/bin/python tools/reparse.py`.
