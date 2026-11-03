"""Разбор подписи поста: пол, категория, размеры, цена, статус «продано»."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .categories import (
    CATEGORIES,
    GENDER_PATTERNS,
    IMPLIED_GENDER,
    LETTER_TO_RU,
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


SIZE_LINE = re.compile(r"(размер|р-р|\bsize\b|өлшем)", re.I)
FIELD_LINE = re.compile(r"^[^\w]*[\w ]{2,30}\s*:")  # «Состав: …», «Цена: …»
LETTER_SIZE = re.compile(r"(?<![A-Za-zА-Яа-я])(XXS|XS|XXXL|XXL|XL|[2-5]XL|S|M|L)(?![A-Za-zА-Яа-я])")
NUMBER_RANGE = re.compile(r"(?<!\d)(?<!\d[.,])(\d{2}(?:[.,]5)?)\s*[-–—]\s*(\d{2}(?:[.,]5)?)(?!\d|[.,]\d)")
NUMBER = re.compile(r"(?<!\d)(?<!\d[.,])(\d{2}(?:[.,]5)?)(?!\d|[.,]\d)(?!\s*(?:см|cm|%|мм|кг|г\b))")
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
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    head = "\n".join(lines[:3]).lower()

    result = ParsedPost(title=_title(lines))
    result.category = _find_category(head)
    result.gender = (
        _find_gender(head)
        or _find_gender(text.lower())
        or IMPLIED_GENDER.get(result.category or "")
        or default_gender
    )
    # В одном посте может быть несколько размеров, часть из них уже продана:
    # «Размер: S … продано‼️ / Размер: M …». Проданные строки не учитываем.
    chunks = _size_chunks(text)
    available = [c for c, _ in chunks if not SOLD.search(c)]
    sold_lines = {i for c, idx in chunks if SOLD.search(c) for i in idx}
    if chunks:
        result.sizes = parse_sizes("\n".join(available), result.category)
    else:
        result.sizes = parse_sizes(_fallback_size_text(text), result.category)
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


def _find_category(text: str) -> str | None:
    for key, _, patterns in CATEGORIES:
        if any(re.search(p, text) for p in patterns):
            return key
    return None


def _size_chunks(text: str) -> list[tuple[str, list[int]]]:
    """Строки с размером плюс продолжение («по факту подойдёт на 48») и их номера строк."""
    lines = [ln.strip() for ln in text.splitlines()]
    chunks: list[tuple[str, list[int]]] = []
    for i, line in enumerate(lines):
        match = SIZE_LINE.search(line)
        if not match:
            continue
        # «Размер» в середине описания («подходит на любой размер») не берём.
        if re.search(r"[а-яa-z]{3,}", line[: match.start()], re.I):
            continue
        parts, idx = [line[match.end():]], [i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if nxt and not FIELD_LINE.search(nxt) and not SIZE_LINE.search(nxt):
            parts.append(nxt)
            idx.append(i + 1)
        chunks.append(("\n".join(parts), idx))
    return chunks


def _fallback_size_text(text: str) -> str:
    """Строки «Размер» нет: ищем только явные «one size» и многобуквенные размеры."""
    return " ".join(ONE_SIZE.findall(text) + re.findall(r"\b(?:XXS|XS|XXL|XXXL|[2-5]XL)\b", text))


def parse_sizes(text: str, category: str | None = None) -> list[str]:
    """Возвращает размеры: российские для одежды, «W32» для брюк, «38» для обуви, «ONE»."""
    text = text.translate(CYR_TO_LAT)
    sizes: set[str] = set()

    if ONE_SIZE.search(text):
        sizes.add("ONE")

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
        step = 1 if category in SHOE_CATEGORIES or (category in WAIST_CATEGORIES and hi <= 36) else 2
        if step == 2 and int(lo) % 2:
            step = 1
        value = lo
        while value <= hi:
            _add_number(sizes, value, category)
            value += step
    for raw in NUMBER.findall(NUMBER_RANGE.sub(" ", text)):
        value = _num(raw)
        if value is not None:
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
        sizes.add(f"W{label}")
    elif 38 <= value <= 74 and value == int(value):
        sizes.add(label)


def sort_sizes(sizes) -> list[str]:
    def key(size: str):
        if size == "ONE":
            return (2, 0.0)
        if size.startswith("W"):
            return (1, float(size[1:]))
        return (0, float(size))
    return sorted(set(sizes), key=key)


def parse_price(text: str) -> int | None:
    """Минимальная цена в посте — обычно это цена со скидкой."""
    candidates = []
    for match in list(PRICE_WITH_CURRENCY.finditer(text)) + list(PRICE_AFTER_WORD.finditer(text)):
        digits = re.sub(r"\D", "", match.group(1))
        if digits and int(digits) >= 100:
            candidates.append(int(digits))
    return min(candidates) if candidates else None
