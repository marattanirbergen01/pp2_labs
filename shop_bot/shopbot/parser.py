"""Разбор подписи поста: пол, категория, размеры, цена, статус «продано»."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .categories import (
    CATEGORIES,
    GENDER_PATTERNS,
    IMPLIED_GENDER,
    LETTER_TO_RU,
    RANGE_LABEL_CATEGORIES,
    SHOE_CATEGORIES,
    WAIST_CATEGORIES,
)


@dataclass
class ParsedPost:
    title: str = ""
    gender: str | None = None
    category: str | None = None
    sizes: list[str] = field(default_factory=list)
    price: int | None = None
    sold: bool = False

    @property
    def complete(self) -> bool:
        return self.category is not None and bool(self.sizes)

    @property
    def looks_like_product(self) -> bool:
        return self.category is not None or self.price is not None or bool(self.sizes)


SIZE_LINE = re.compile(r"(размер|р-р|\bsize\b|өлшем)", re.I)
FIELD_LINE = re.compile(r"^[^\w]*[\w ]{2,30}\s*:")  # «Состав: …», «Цена: …»
LETTER_SIZE = re.compile(r"(?<![A-Za-zА-Яа-я])(XXS|XS|XXXL|XXL|XL|[2-5]XL|S|M|L)(?![A-Za-zА-Яа-я])")
NOT_A_SIZE = r"(?!\s*(?:см|cm|%|мм|кг|г\b|лет|год|мес))"  # обмеры, возраст
NUMBER_RANGE = re.compile(
    r"(?<!\d)(?<!\d[.,])(\d{2,3}(?:[.,]5)?)\s*[-–—]\s*(\d{2,3}(?:[.,]5)?)(?!\d|[.,]\d)" + NOT_A_SIZE)
NUMBER = re.compile(r"(?<!\d)(?<!\d[.,])(\d{2,3}(?:[.,]5)?)(?!\d|[.,]\d)" + NOT_A_SIZE)
# «отлично подойдёт на 48», «по факту 46» — размер без слова «Размер».
FIT_LINE = re.compile(r"(подойд[её]т|подойдут|по факту)[^\d\n]{0,25}(?=\d)", re.I)
# Детский рост 74–176 см: «122–128», «146».
KIDS_HEIGHT = re.compile(r"(?<!\d)(7[4-9]|[89]\d|1[0-7]\d)(?!\d)" + NOT_A_SIZE)
ONE_SIZE = re.compile(r"one\s*size|единый размер|универсальный размер|безразмер", re.I)

CURRENCY = r"(?:тг|тенге|₸|kzt|tg)(?![a-zа-я])"
AMOUNT = r"(\d{1,3}(?:[  .,]\d{3})+|\d{3,7})"
PRICE_WITH_CURRENCY = re.compile(AMOUNT + r"\s*" + CURRENCY, re.I)
PRICE_AFTER_WORD = re.compile(r"(?:цена|баға|price)[^\d\n]{0,20}" + AMOUNT, re.I)

SOLD = re.compile(r"\bпродан[оаы]?\b|\bsold\b|нет в наличии|сатылды", re.I)

# Латинские буквы, которые продавцы часто набирают кириллицей.
CYR_TO_LAT = str.maketrans({"М": "M", "Х": "X", "С": "S", "Ѕ": "S"})


def parse_post(text: str, default_gender: str | None = None) -> ParsedPost:
    text = text or ""
    # Строки-пометки вроде «‼️продано‼️» над названием — не название товара.
    lines = [ln.strip() for ln in text.splitlines()
             if ln.strip() and not (SOLD.search(ln) and len(re.findall(r"\w+", ln)) <= 2)]
    head = "\n".join(lines[:3]).lower()

    result = ParsedPost(title=_title(lines))
    result.category = _find_category(lines)
    explicit_gender = _find_gender(head) or _find_gender(text.lower())

    # В одном посте может быть несколько размеров, часть из них уже продана:
    # «Размер: S … продано‼️ / Размер: M …». Проданные строки не учитываем.
    chunks = _size_chunks(text)
    available = [c for c, _ in chunks if not SOLD.search(c)]
    sold_lines = {i for c, idx in chunks if SOLD.search(c) for i in idx}
    size_text = "\n".join(available) if chunks else _fallback_size_text(text)
    if not explicit_gender and KIDS_HEIGHT.search(size_text):
        explicit_gender = "kids"  # «Размер: 122–128» — это рост ребёнка
    result.gender = explicit_gender or IMPLIED_GENDER.get(result.category or "") or default_gender
    result.sizes = parse_sizes(size_text, result.category, kids=result.gender == "kids")
    result.price = parse_price(text)
    rest = "\n".join(ln for i, ln in enumerate(text.splitlines()) if i not in sold_lines)
    result.sold = bool(SOLD.search(rest)) or bool(chunks and not available)
    return result


def _title(lines: list[str]) -> str:
    for line in lines:
        clean = re.sub(r"[^\w\s\-&'«»\"().,]", "", line).strip(" -")
        if clean:
            return clean[:80]
    return ""


def _find_gender(text: str) -> str | None:
    found = [g for g, patterns in GENDER_PATTERNS.items() if any(re.search(p, text) for p in patterns)]
    if "unisex" in found or {"men", "women"} <= set(found):
        return "unisex"
    return found[0] if found else None


def _find_category(lines: list[str]) -> str | None:
    """Сначала название (первая строка): побеждает самое раннее слово. Потом первые 3 строки."""
    if lines:
        title = lines[0].lower()
        best = None
        for order, (key, _, patterns) in enumerate(CATEGORIES):
            for pattern in patterns:
                match = re.search(pattern, title)
                if match and (best is None or (match.start(), order) < best[0]):
                    best = ((match.start(), order), key)
        if best:
            return best[1]
    head = "\n".join(lines[:3]).lower()
    for key, _, patterns in CATEGORIES:
        if any(re.search(p, head) for p in patterns):
            return key
    return None


def _size_chunks(text: str) -> list[tuple[str, list[int]]]:
    """Строки с размером плюс продолжение («по факту подойдёт на 48») и их номера строк."""
    lines = [ln.strip() for ln in text.splitlines()]
    chunks: list[tuple[str, list[int]]] = []
    used: set[int] = set()
    for i, line in enumerate(lines):
        match = SIZE_LINE.search(line)
        # «Размер» в середине описания («подходит на любой размер») не берём.
        if not match or re.search(r"[а-яa-z]{3,}", line[: match.start()], re.I):
            continue
        parts, idx = [line[match.end():]], [i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if nxt and not FIELD_LINE.search(nxt) and not SIZE_LINE.search(nxt):
            parts.append(nxt)
            idx.append(i + 1)
        chunks.append(("\n".join(parts), idx))
        used.update(idx)
    for i, line in enumerate(lines):
        if i not in used and (match := FIT_LINE.search(line)):
            chunks.append((line[match.end():], [i]))
    return chunks


def _fallback_size_text(text: str) -> str:
    """Строки «Размер» нет: ищем только явные «one size» и многобуквенные размеры."""
    return " ".join(ONE_SIZE.findall(text) + re.findall(r"\b(?:XXS|XS|XXL|XXXL|[2-5]XL)\b", text))


def parse_sizes(text: str, category: str | None = None, kids: bool = False) -> list[str]:
    """Размеры: российские для одежды (W32 у брюк тоже переводится в русский — 48), «38» для обуви, «ONE»,
    диапазоны «122-128» для детей (рост) и колготок/носков."""
    text = text.translate(CYR_TO_LAT)
    if re.search(r"\bW\s?\d{2}\b", text):
        text = re.sub(r"\bL\s?\d{2}\b", " ", text)  # «W30 L32»: L — длина штанин, не размер
    sizes: set[str] = set()
    as_ranges = kids or category in RANGE_LABEL_CATEGORIES

    if ONE_SIZE.search(text):
        sizes.add("ONE")

    if not kids:
        letters = list(LETTER_TO_RU)
        for a, b in re.findall(LETTER_SIZE.pattern + r"\s*[-–—/]\s*" + LETTER_SIZE.pattern, text):
            a, b = _norm_letter(a), _norm_letter(b)
            if a in letters and b in letters and letters.index(a) <= letters.index(b):
                sizes.update(LETTER_TO_RU[x] for x in letters[letters.index(a): letters.index(b) + 1])
        for letter in LETTER_SIZE.findall(text):
            sizes.add(LETTER_TO_RU[_norm_letter(letter)])

    for a, b in NUMBER_RANGE.findall(text):
        lo, hi = _num(a), _num(b)
        if lo is None or hi is None or not 0 < hi - lo <= 16:
            continue
        if as_ranges:
            if 16 <= lo and hi <= 176:
                sizes.add(f"{int(lo)}-{int(hi)}")
            continue
        step = 1 if category in SHOE_CATEGORIES or (category in WAIST_CATEGORIES and hi <= 36) else 2
        if step == 2 and int(lo) % 2:
            step = 1
        value = lo
        while value <= hi:
            _add_number(sizes, value, category)
            value += step
    for raw in NUMBER.findall(NUMBER_RANGE.sub(" ", text)):
        value = _num(raw)
        if value is None:
            continue
        if as_ranges:
            if 16 <= value <= 176 and value == int(value):
                sizes.add(str(int(value)))
        else:
            _add_number(sizes, value, category)

    return sort_sizes(sizes)


def _norm_letter(letter: str) -> str:
    letter = letter.upper()
    return {"XXXL": "3XL", "2XL": "XXL"}.get(letter, letter)


def _num(raw: str) -> float | None:
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def _add_number(sizes: set[str], value: float, category: str | None) -> None:
    label = str(int(value)) if value == int(value) else str(value)
    if category in SHOE_CATEGORIES:
        if 16 <= value <= 48:
            sizes.add(label)
    elif category in WAIST_CATEGORIES and 23 <= value <= 36:
        # Американский размер по талии (W) -> русский: W28 = 44, W30 = 46, W32 = 48.
        ru = int(value) + 16
        sizes.update({str(ru)} if ru % 2 == 0 else {str(ru - 1), str(ru + 1)})
    elif 38 <= value <= 74 and value == int(value):
        sizes.add(label)


def sort_sizes(sizes) -> list[str]:
    def key(size: str):
        if size == "ONE":
            return (2, 0.0)
        if size.startswith("W"):
            return (1, float(size[1:]))
        return (0, float(size.split("-")[0]))
    return sorted(set(sizes), key=key)


def parse_price(text: str) -> int | None:
    """Минимальная цена в посте — обычно это цена со скидкой."""
    candidates = []
    for match in list(PRICE_WITH_CURRENCY.finditer(text)) + list(PRICE_AFTER_WORD.finditer(text)):
        digits = re.sub(r"\D", "", match.group(1))
        if digits and int(digits) >= 100:
            candidates.append(int(digits))
    return min(candidates) if candidates else None
