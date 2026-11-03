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


TWO_SIZES_ONE_SOLD = """👚 Женская кофточка Blue Motion

💛 Цвет: жёлтый
🧵 Ткань: хлопок
📏 Размер: S — большемерит, подойдет на 44–
46 ✅ продано‼️
📏 Размер: M — подойдет на 46–48✅
🇩🇪 Качество: Германия

💰 Цена: 3 850 ₸
Со скидкой -30%: 2 700 тг

🚚 Доставка по всему Казахстану
➕ Каспи Red +10%
📲 WhatsApp: wa.me/77073017434"""

SLIM_SIZE = """Женская блузка
📏 Размер: 48 ✅
стройный 50
🇩🇪 Качество: Германия
💰 Цена: 4 750 ₸
Со скидкой -30%: 3 325 тг"""


def test_one_size_sold_other_available():
    p = parse_post(TWO_SIZES_ONE_SOLD)
    assert (p.gender, p.category) == ("women", "hoodies")
    assert p.sizes == ["46", "48"]  # S (44–46) продан, остаётся M (46–48)
    assert not p.sold
    assert p.price == 2700


def test_all_sizes_sold():
    p = parse_post(TWO_SIZES_ONE_SOLD.replace("46–48✅", "46–48 продано"))
    assert p.sold


def test_slim_size_on_next_line():
    p = parse_post(SLIM_SIZE)
    assert p.sizes == ["48", "50"] and p.price == 3325


# Названия реальных постов, которые раньше не распознавались.
REAL_TITLES = {
    "🩵 Женские капри": ("pants", "women"),
    "🤍 Женские кюлоты": ("pants", "women"),
    "💗 Женская маечка": ("tshirts", "women"),
    "👒 Женская шляпа": ("accessories", "women"),
    "🩵 Велосипедки на девочку 🩵": ("shorts", "kids"),
    "🩳 Мужские шорты-бриджи": ("shorts", "men"),
    "🏃‍♀️ Женские термолосины": ("pants", "women"),
    "👗 Женское платье-рубашка": ("dresses", "women"),
    "👚 Комплект из 2 женских лонгсливов Blue Motion 🇩🇪": ("hoodies", "women"),
    "🩳 Комплект женских шорт Blue Motion 🇩🇪": ("shorts", "women"),
    "🏃‍♀️ Женская спортивная мастерка Crane 🇩🇪": ("hoodies", "women"),
    "🖤 Женский брючный комбинезон Esmara": ("suits", "women"),
    "🧦 Тёплые детские колготки Lily & Dan 🇩🇪": ("hosiery", "kids"),
    "🧦🎀 Термогольфы на девочку Lily & Dan": ("hosiery", "kids"),
    "🧦🐻 Тёплые термоноски": ("hosiery", None),
    "🖤 Женское корректирующее бельё": ("underwear", "women"),
    "🖤 Мужские кальсоны Livergy": ("underwear", "men"),
    "🐆 Яркое боди в дерзком стиле 🐆": ("underwear", None),
    "🩵 Женский палантин PIECES": ("accessories", "women"),
    "💙 Женская джинсовая куртка ONLY": ("outerwear", "women"),
    "🖤 Дублёнка ADPT": ("outerwear", None),
    "♥️ Женская кофта-туника": ("hoodies", "women"),
    "🌿 ЖЕНСКАЯ ТУНИКА Sheego Ladies 🇩🇪": ("shirts", "women"),
    "🩶 Женская безрукавка": ("tshirts", "women"),
    "💚💖 Мужская спортивная олимпийка": ("hoodies", "men"),
    "🌿 Мужские слаксы Jack & Jones": ("pants", "men"),
    "🧡 Кофта-пончо от Sheego — Германия 🇩🇪": ("hoodies", None),
    "Потрясающий стильный жакет-накидка 🖤✨": ("outerwear", None),
    "🖤✨ Юбка-шорты для девочки": ("skirts", "kids"),
    "👕🤎 Поло на мальчика": ("tshirts", "kids"),
}


def test_real_titles():
    wrong = {}
    for title, expected in REAL_TITLES.items():
        p = parse_post(title)
        if (p.category, p.gender) != expected:
            wrong[title] = (p.category, p.gender)
    assert wrong == {}


def test_kids_sizes_are_height_ranges():
    p = parse_post("🧦 Детские колготки Lily & Dan\n📏 Размер: 122–128, 6–8 лет\n💰 Цена: 2 500 тг")
    assert (p.category, p.gender, p.sizes) == ("hosiery", "kids", ["122-128"])
    p = parse_post("Кофточка на девочку в ярко-розовом цвете 💖\n\nРазмер 122–128 — на 7–8 лет")
    assert (p.gender, p.sizes) == ("kids", ["122-128"])
    # Рост без пометки «детское» тоже значит детское.
    p = parse_post("🌸 Кофта\n📏 Размер: 146–152 ✅", default_gender="women")
    assert (p.gender, p.sizes) == ("kids", ["146-152"])


def test_fit_line_without_size_word():
    p = parse_post("🖤 Женский брючный комбинезон Esmara\n✨ Цвет: чёрный\n📏 Подойдет на 48–50 ✅")
    assert p.sizes == ["48", "50"]
    p = parse_post("Мужской тёплый термо-лонгслив\nТермолонгслив в размере M, отлично подойдёт на 48 размер.")
    assert p.sizes == ["48"]


def test_sold_marker_line_is_not_title():
    p = parse_post("‼️продано‼️\n\n🖤 Женские лосины Blue Motion\n📏 Размер: XL, 50–52 ✅")
    assert p.title == "Женские лосины Blue Motion"
    assert (p.category, p.sold) == ("pants", True)


def test_greeting_is_not_a_product():
    p = parse_post("🌸 Девочки, всем доброе утро! ☀️\n\nЖелаем вам прекрасного дня и удачных покупок!")
    assert not p.looks_like_product
    assert not parse_post("Елена, благодарю 🫶🫂").looks_like_product
