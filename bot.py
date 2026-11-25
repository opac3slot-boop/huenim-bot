
import asyncio
import os
import random
import re
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message


# =========================
# НАСТРОЙКИ
# =========================

HUENIM_CHANCE = 0.30
MEMORY_CHANCE = 0.07

DB_NAME = "memory.db"
MAX_MEMORY_LENGTH = 300


# =========================
# 1. ХУЕНИМЫ — КОД ДРУГА
# =========================

SPECIAL_WORDS = {
    "пылесос": "хуесос",
    "крокодил": "хуедил",
    "самокат": "хуекат",
    "бутерброд": "хуерброд",
    "бегемот": "хуемот",
    "мандарин": "хуерин",
    "паровоз": "хуевоз",
}

VOWELS = "аеёиоуыэюя"

VOWEL_MAP = {
    "а": "я",
    "о": "ё",
    "у": "ю",
    "ы": "и",
    "э": "е",
}


def make_huenim(word: str) -> str:
    original = word
    lower_word = word.lower()

    if lower_word in SPECIAL_WORDS:
        result = SPECIAL_WORDS[lower_word]
    else:
        first_vowel_idx = -1

        for i, char in enumerate(lower_word):
            if char in VOWELS:
                first_vowel_idx = i
                break

        if first_vowel_idx == -1:
            result = "ху" + lower_word
        else:
            first_vowel = lower_word[first_vowel_idx]
            mapped_vowel = VOWEL_MAP.get(first_vowel, first_vowel)
            result = "ху" + mapped_vowel + lower_word[first_vowel_idx + 1:]

    if original.isupper() and len(original) > 1:
        return result.upper()

    if original[0].isupper():
        return result.capitalize()

    return result


# =========================
# 2. ОСКОРБЛЕНИЯ
# =========================

MALE_INSULTS = [
    r"хуесос(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"хуеплет(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"хуеглот(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"хуил(?:а|ы|е|у|ой|ами|ах)?",
    r"пиздобол(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"пиздюк(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"мудак(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"мудил(?:а|ы|е|у|ой|ами|ах)?",
    r"мудозвон(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"еблан(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"ебанат(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"ебанут(?:ый|ого|ому|ым|ом|ые|ых|ыми)",
    r"ебнут(?:ый|ого|ому|ым|ом|ые|ых|ыми)",
    r"долбоеб(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"уебок(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"урод(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"уебище(?:м|а|й|и)?",
    r"ублюдок(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"упиздок(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"гандон(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"гондон(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"говноед(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"говнюк(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"глуп(?:ый|ого|ому|ым|ом|ые|ых|ыми)",
    r"идиот(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"дурак(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"дебил(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"кретин(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"кончен(?:ный|ый|ного|ого|ному|ому|ным|ым|ном|ом|ные|ых|ыми)",
    r"придурок(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"болван(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"туп(?:ой|ого|ому|ым|ом|ые|ых|ыми)",
    r"недоумок(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"бестолоч(?:ь|и|ью|ей|ам|ами|ах)",
    r"бездар(?:ь|я|ю|ем|и|ей|ям|ями|ях)",
    r"мерзав(?:ец|ца|цу|цем|цы|цев|цам|цами|цах)",
    r"подлец(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"негодяй(?:я|ю|ем|и|ев|ям|ями|ях)?",
    r"подонок(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"олух(?:а|у|ом|е|и|ов|ам|ами|ах)?",
    r"балбес(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"раздолбай(?:я|ю|ем|и|ев|ям|ями|ях)?",
    r"оболтус(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
]

FEMALE_INSULTS = [
    r"сучк(?:а|и|е|у|ой|ам|ами|ах)",
    r"твар(?:ь|и|ью|ей|ям|ями|ях)",
    r"ебанашк(?:а|и|е|у|ой|ам|ами|ах)",
    r"ебанут(?:ая|ой|ую|ые|ых|ыми)",
    r"ебнут(?:ая|ой|ую|ые|ых|ыми)",
    r"ебланк(?:а|и|е|у|ой|ам|ами|ах)",
    r"долбоебк(?:а|и|е|у|ой|ам|ами|ах)",
    r"кончен(?:ная|ая|ной|ой|ную|ую|ные|ых|ыми)",
    r"мраз(?:ь|и|ью|ей|ям|ями|ях)",
    r"паскуд(?:а|ы|е|у|ой|ам|ами|ах)",
    r"стерв(?:а|ы|е|у|ой|ам|ами|ах)",
    r"дур(?:а|ы|е|у|ой|ам|ами|ах)",
    r"идиотк(?:а|и|е|у|ой|ам|ами|ах)",
    r"дебилк(?:а|и|е|у|ой|ам|ами|ах)",
    r"туп(?:ая|ой|ую|ые|ых|ыми)",
    r"негодяйк(?:а|и|е|у|ой|ам|ами|ах)",
    r"овц(?:а|ы|е|у|ой|ам|ами|ах)",
    r"коз(?:а|ы|е|у|ой|ам|ами|ах)",
]


def compile_insults(patterns):
    return [
        re.compile(
            r"(?<!\w)(?:" + pattern + r")(?!\w)",
            re.IGNORECASE
        )
        for pattern in patterns
    ]


MALE_PATTERNS = compile_insults(MALE_INSULTS)
FEMALE_PATTERNS = compile_insults(FEMALE_INSULTS)


def find_insult(text):
    # Только для проверки оскорблений:
    # Е и Ё считаются одинаковыми.
    normalized_text = text.lower().replace("ё", "е")

    matches = []

    for pattern in MALE_PATTERNS:
        match = pattern.search(normalized_text)
        if match:
            matches.append((match.start(), "папаша твой"))

    for pattern in FEMALE_PATTERNS:
        match = pattern.search(normalized_text)
        if match:
            matches.append((match.start(), "мамка твоя"))

    if not matches:
        return None

    matches.sort(key=lambda item: item[0])
    return matches[0][1]


# =========================
# 3. ПАМЯТЬ БОТА
# =========================

def init_database():
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL UNIQUE
            )
        """)


def remember_text(text):
    if not text or len(text) > MAX_MEMORY_LENGTH:
        return

    with sqlite3.connect(DB_NAME) as connection:
        connection.execute(
            "INSERT OR IGNORE INTO memories (text) VALUES (?)",
            (text,)
        )

        words = re.findall(
            r"[А-Яа-яЁёA-Za-z0-9]+(?:[-'][А-Яа-яЁёA-Za-z0-9]+)*",
            text
        )

        for word in words:
            if len(word) >= 2:
                connection.execute(
                    "INSERT OR IGNORE INTO memories (text) VALUES (?)",
                    (word,)
                )


def get_random_memory():
    with sqlite3.connect(DB_NAME) as connection:
        result = connection.execute(
            "SELECT text FROM memories ORDER BY RANDOM() LIMIT 1"
        ).fetchone()

    return result[0] if result else None


# =========================
# 4. ОСНОВНАЯ РАБОТА БОТА
# =========================

async def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise RuntimeError("BOT_TOKEN не задан")

    init_database()

    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(F.text)
    async def handle_message(message: Message):
        if message.from_user and message.from_user.is_bot:
            return

        original_text = message.text.strip()

        if not original_text:
            return

        # Сначала проверяем оскорбления
        insult_response = find_insult(original_text)

        if insult_response:
            remember_text(original_text)
            await message.answer(insult_response)
            return

        # Получаем старое воспоминание
        memory = get_random_memory()

        # Запоминаем новое сообщение
        remember_text(original_text)

        # Спонтанное сообщение — 7%
        if memory and random.random() < MEMORY_CHANCE:
            await message.answer(memory)
            return

        # Проверяем, является ли сообщение одним словом
        clean_text = re.sub(
            r"^[^\wА-Яа-яЁё]+|[^\wА-Яа-яЁё]+$",
            "",
            original_text
        )

        if not re.fullmatch(
            r"[А-Яа-яЁё]+(-[А-Яа-яЁё]+)*",
            clean_text
        ):
            return

        if len(clean_text) < 4:
            return

        # Хуенимы — 30%
        if random.random() >= HUENIM_CHANCE:
            return

        response = make_huenim(clean_text)

        if response.lower() != clean_text.lower():
            await message.answer(response)

        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
