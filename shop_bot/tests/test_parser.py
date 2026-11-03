from shopbot.parser import parse_post, parse_price, parse_sizes

CARDIGAN = """✨ Нежная кофточка кардиган ✨
❄️ Тёплая и в то же время элегантная
🏷 Бренд: NA-KD
🇸🇪 Качество: Швеция

💰 Цена: 14 350 тг
Со скидкой —40%: 8.610 тг

🖤 Размер: 46, стройная 48

👗 Особенности модели:
🔷 Цвет — чёрный
🔷 Плетение — «лапша»
🔷 Модель с запахом, с одной стороны есть отверстие для пояска
🔷 Пояс можно завязать сзади или сбоку
🔷 Полный длинный рукав
💫 Сочетается с брюками, юбками или джинсами — шикарно смотрится в любом образе

🧵 Состав ткани: 50% акрил, 50% хлопок

📦🚚 Доставка по всему Казахстану
📲 WhatsApp: wa.me/77073017434"""

TSHIRT = """💜 Женская футболка VILA

✨ Нежная и стильная базовая модель в красивом сиреневом цвете — отличный вариант на каждый день 🌸

⭐ Бренд: VILA
🔥 Коллекция: Bestseller
🇩🇰 Качество: Дания
🧵 Ткань: хлопок
📏 Размер: M,
по факту подойдёт на 48 ✅

💰 Цена: 5 500 тг
Скидка -40%: 3.300 тг

🚚 Доставка по всему Казахстану
📲 Для заказа: wa.me/77073017434"""

BLOUSE = """✨ ЖЕНСКАЯ БЛУЗА ✨

Элегантная и стильная модель в аккуратную полоску 🤍
Удлинённый силуэт смотрится очень красиво и легко вписывается как в повседневные, так и в более нарядные образы.

▫️ Бренд: Sheego
▫️ Германия 🇩🇪
▫️ Размер: 54 ✅
▫️ Состав: вискоза с добавлением эластана — мягкая, комфортная и приятная к телу ткань 🌿
▫️ Застёгивается спереди на пуговицы до половины
▫️ В комплекте поясок 🎀
▫️ Удлинённая модель

💰 Цена: 8 500 ₸
Скидка -40%: 5.100 тг

📦🚚 Доставка по всему Казахстану
wa.me/77073017434"""

CARGO = """🖤👖 Мужские брюки Cargo премиального качества
🔥 Шикарная модель в чёрном цвете — стильная, брутальная и очень практичная
💼 Отличный вариант на каждый день
✨ Карго всегда в тренде — удобно, модно и универсально

📏 Размер: Size 32
📐 Полуобхват талии: 42 см
📐 Полуобхват бёдер: 54 см
📐 Полная длина: 102 см
🧵 Ткань: хлопок с эластаном — плотные, комфортные, отлично тянутся
🇩🇰 Качество: Дания, премиальное
💰 Цена: 14 500 тг
🎉 Со скидкой -20%: 11.600 тг

🏷 Бренд: Only & Sons

📦🚚 Доставка по всему Казахстану
📲 WhatsApp: wa.me/77073017434"""


def test_cardigan():
    p = parse_post(CARDIGAN, default_gender="women")
    assert p.title == "Нежная кофточка кардиган"
    assert (p.gender, p.category) == ("women", "hoodies")
    assert p.sizes == ["46", "48"]
    assert p.price == 8610
    assert not p.sold and p.complete


def test_tshirt_letter_size_and_fact_size():
    p = parse_post(TSHIRT)
    assert (p.gender, p.category) == ("women", "tshirts")
    assert p.sizes == ["46", "48"]
    assert p.price == 3300


def test_blouse():
    p = parse_post(BLOUSE)
    assert (p.gender, p.category) == ("women", "shirts")
    assert p.sizes == ["54"]
    assert p.price == 5100


def test_cargo_waist_size_ignores_measurements():
    p = parse_post(CARGO, default_gender="women")
    assert (p.gender, p.category) == ("men", "pants")
    assert p.sizes == ["W32"]
    assert p.price == 11600


def test_sold_marker():
    assert parse_post(TSHIRT + "\n\n❌ ПРОДАНО").sold
    assert not parse_post(TSHIRT).sold


def test_size_variants():
    assert parse_sizes("42-48") == ["42", "44", "46", "48"]
    assert parse_sizes("S-L") == ["44", "46", "48"]
    assert parse_sizes("36-39", "shoes") == ["36", "37", "38", "39"]
    assert parse_sizes("XL, 2XL") == ["50", "52"]
    assert parse_sizes("ХL") == ["50"]  # кириллическая Х
    assert parse_sizes("one size") == ["ONE"]


def test_price_variants():
    assert parse_price("Цена 25000") == 25000
    assert parse_price("Было 20 000 тг, сейчас 15 000 тг") == 15000
    assert parse_price("скидка 40%") is None


def test_no_text():
    p = parse_post("")
    assert p.category is None and not p.complete
