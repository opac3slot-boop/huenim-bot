
import asyncio
import os
import random
import re
import sqlite3

from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher
from aiogram.types import Message


# =========================
# НАСТРОЙКИ
# =========================

HUENIM_CHANCE = 0.30
MEMORY_CHANCE = 0.07

CATCHPHRASE_CHANCE = 0.02
GESTURE_CHANCE = 0.02

DB_NAME = "memory.db"
MAX_MEMORY_LENGTH = 300

# Московское время: UTC+3
MOSCOW_TIME = timezone(timedelta(hours=3))


# =========================
# ХУЕНИМЫ
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

            result = (
                "ху"
                + mapped_vowel
                + lower_word[first_vowel_idx + 1:]
            )

    if original.isupper() and len(original) > 1:
        return result.upper()

    if original[0].isupper():
        return result.capitalize()

    return result


# =========================
# МУЖСКИЕ ОСКОРБЛЕНИЯ
# =========================

MALE_INSULTS = [
    r"хуесос(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"хуеплет(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"хуеглот(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"хуил(?:а|ы|е|у|ой|ами|ах)?",
    r"пиздобол(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
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
    r"дибил(?:а|у|ом|е|ы|ов|ам|ами|ах)?",
    r"ебач(?:а|у|ем|е|и|ей|ам|ами|ах)?",
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


# =========================
# ЖЕНСКИЕ ОСКОРБЛЕНИЯ
# =========================

FEMALE_INSULTS = [
    r"сучк(?:а|и|е|у|ой|ам|ами|ах)",
    r"твар(?:ь|и|ью|ей|ям|ями|ях)",
    r"ебанашк(?:а|и|е|у|ой|ам|ами|ах)",
    r"ебанут(?:ая|ой|ую|ые|ых|ыми)",
    r"ебнут(?:ая|ой|ую|ые|ых|ыми)",
    r"ебланк(?:а|и|е|у|ой|ам|ами|ах)",
    r"долбоебк(?:а|и|е|у|ой|ам|ами|ах)",
    r"ебачих(?:а|и|е|у|ой|ам|ами|ах)",
    r"кончен(?:ная|ая|ной|ой|ную|ую|ные|ых|ыми)",
    r"мраз(?:ь|и|ью|ей|ям|ями|ях)",
    r"паскуд(?:а|ы|е|у|ой|ам|ами|ах)",
    r"стерв(?:а|ы|е|у|ой|ам|ами|ах)",
    r"дур(?:а|ы|е|у|ой|ам|ами|ах)",
    r"идиотк(?:а|и|е|у|ой|ам|ами|ах)",
    r"дебилк(?:а|и|е|у|ой|ам|ами|ах)",
    r"дибилк(?:а|и|е|у|ой|ам|ами|ах)",
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


def normalized_text(text: str) -> str:
    return text.lower().replace("ё", "е")


def get_all_insults(text: str):
    text = normalized_text(text)
    found = set()

    for pattern in MALE_PATTERNS + FEMALE_PATTERNS:
        for match in pattern.finditer(text):
            found.add((match.start(), match.end()))

    return sorted(found)


def find_insult(text):
    text = normalized_text(text)
    matches = []

    for pattern in MALE_PATTERNS:
        match = pattern.search(text)

        if match:
            matches.append((match.start(), "папаша твой"))

    for pattern in FEMALE_PATTERNS:
        match = pattern.search(text)

        if match:
            matches.append((match.start(), "мамка твоя"))

    if not matches:
        return None

    matches.sort(key=lambda item: item[0])

    return matches[0][1]


# =========================
# БАЗА ДАННЫХ
# =========================

def init_database():
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL UNIQUE
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS daily_insults (
                day TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (day, user_id)
            )
        """)


# =========================
# ПАМЯТЬ БОТА
# =========================

def remember_exact_text(text):
    if not text:
        return

    with sqlite3.connect(DB_NAME) as connection:
        connection.execute(
            "INSERT OR IGNORE INTO memories (text) VALUES (?)",
            (text,)
        )


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
# ЕЖЕДНЕВНАЯ СТАТИСТИКА
# =========================

def get_today():
    return datetime.now(MOSCOW_TIME).date().isoformat()


def count_user_insults(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    if not message.from_user or message.from_user.is_bot:
        return

    text = message.text or message.caption or ""

    if not text:
        return

    insults = get_all_insults(text)
    amount = len(insults)

    if amount == 0:
        return

    user = message.from_user
    today = get_today()

    with sqlite3.connect(DB_NAME) as connection:
        connection.execute("""
            INSERT INTO daily_insults (
                day, user_id, username, first_name, count
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(day, user_id)
            DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                count = daily_insults.count + excluded.count
        """, (
            today,
            user.id,
            user.username,
            user.first_name,
            amount
        ))


def make_user_mention(user_id, username, first_name):
    """
    Возвращает обычный текст, без HTML-ссылок
    и без ссылки на профиль Telegram.
    """
    if username:
        return f"@{username}"

    return first_name or "пользователь"


def insult_word_form(count):
    """
    Правильное склонение слова «оскорбление».
    """
    if 11 <= count % 100 <= 14:
        return "оскорблений"

    last_digit = count % 10

    if last_digit == 1:
        return "оскорбление"

    if 2 <= last_digit <= 4:
        return "оскорбления"

    return "оскорблений"


def get_daily_leader():
    today = get_today()

    with sqlite3.connect(DB_NAME) as connection:
        rows = connection.execute("""
            SELECT user_id, username, first_name, count
            FROM daily_insults
            WHERE day = ?
            ORDER BY count DESC
        """, (today,)).fetchall()

    if not rows:
        return None

    highest_count = rows[0][3]

    leaders = [
        row for row in rows
        if row[3] == highest_count
    ]

    return random.choice(leaders)


# =========================
# ОБЩИЕ ТРИГГЕРЫ
# =========================

PIIZDYUK_PATTERN = re.compile(
    r"(?<!\w)п(?:и|е)здюк(?!\w)",
    re.IGNORECASE
)

ADVICE_PATTERN = re.compile(
    r"(?<!\w)п(?:и|е)здюк\s+(?:дай\s+совет|че\s+делать)(?!\w)",
    re.IGNORECASE
)

DAILY_LEADER_PATTERN = re.compile(
    r"(?<!\w)п(?:и|е)здюк\s+кто\s+дохуя\s+пиздит(?!\w)",
    re.IGNORECASE
)

SAY_PATTERN = re.compile(
    r"(?<!\w)п(?:и|е)здюк\s+скажи(?:\s+|$)(.*)",
    re.IGNORECASE | re.DOTALL
)

SHCHELBAN_PATTERN = re.compile(
    r"(?<!\w)щелбан(?!\w)",
    re.IGNORECASE
)


# =========================
# СЛУЧАЙНЫЕ ОТВЕТЫ
# =========================

PIIZDYUK_RESPONSES = [
    "чего",
    "а?",
    "че",
    "че надо",
    "кто звал",
    "че звали",
    "ты мне?",
    "че опять",
    "чуть что сразу пиздюк",
    "я занят",
    "сам пиздюк",
    "да иду я",
    "да иду блять",
    "да тут я",
    "я тут",
    "ну?",
]

ADVICE_RESPONSES = [
    "обоссы",
    "въеби",
    "дай по ебалу",
    "съебись",
    "забей хуй",
    "шли нахуй",
    "иди поспи",
    "дай пизды",
    "не еби мозги",
    "хз",
    "не позорься",
    "поплачь",
    "отпизди",
    "нахуй оно тебе надо",
    "да забей",
]

SHCHELBAN_RESPONSES = [
    "ай блять",
    "да за что",
    "че за хуйня",
    "щас получишь",
    "руки не распускай",
    "я это запомнил",
    "ало нахуй",
]

CATCHPHRASES = [
    "ДИНАСТИЯЯЯЯЯЯЯ",
    "сиксевен",
    "СИКСЕВЕН",
    "я тебя могну",
]

GESTURES = [
    "пиздюк обнял",
    "пиздюк отвесил щелбан",
]


# =========================
# ЩЕЛБАН: ПОИСК ПОЛУЧАТЕЛЯ
# =========================

def get_mentioned_username(text):
    match = re.search(
        r"(?<!\w)@([A-Za-z0-9_]{5,32})",
        text
    )

    if match:
        return match.group(1)

    return None


def get_reply_target(message: Message):
    replied = message.reply_to_message

    if not replied or not replied.from_user:
        return None

    return replied.from_user


# =========================
# ЗАПУСК БОТА
# =========================

async def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise RuntimeError("BOT_TOKEN не задан")

    init_database()

    bot = Bot(token=token)
    dp = Dispatcher()

    bot_user = await bot.get_me()
    bot_user_id = bot_user.id

    @dp.message()
    async def handle_message(message: Message):
        if not message.from_user:
            return

        if message.from_user.is_bot:
            return

        original_text = (
            message.text or message.caption or ""
        ).strip()

        # Считаем оскорбления участника
        count_user_insults(message)

        # =====================================
        # 1. «ПИЗДЮК СКАЖИ ...»
        # =====================================

        say_match = SAY_PATTERN.search(original_text)

        if say_match:
            phrase = say_match.group(1).strip()

            if phrase:
                remember_exact_text(phrase)
                await message.reply(phrase)

            return

        # =====================================
        # 2. «ПИЗДЮК ДАЙ СОВЕТ» / «ЧЕ ДЕЛАТЬ»
        # =====================================

        if ADVICE_PATTERN.search(original_text):
            await message.reply(
                random.choice(ADVICE_RESPONSES)
            )
            return

        # =====================================
        # 3. «КТО ДОХУЯ ПИЗДИТ»
        # =====================================

        if DAILY_LEADER_PATTERN.search(original_text):
            leader = get_daily_leader()

            if leader is None:
                await message.reply(
                    "сегодня никто не распизделся"
                )
                return

            user_id, username, first_name, count = leader

            mention = make_user_mention(
                user_id,
                username,
                first_name
            )

            word_form = insult_word_form(count)

            await message.reply(
                f"сегодня {mention} дохуя пиздит"
                f"({count} {word_form})"
            )
            return

        # =====================================
        # 4. ЩЕЛБАН
        # =====================================

        if SHCHELBAN_PATTERN.search(original_text):
            target = get_reply_target(message)

            # Если щелбан прилетел по самому боту
            if target and target.id == bot_user_id:
                await message.reply(
                    random.choice(SHCHELBAN_RESPONSES)
                )
                return

            # Если щелбан прилетел по участнику группы
            if target:
                mention = make_user_mention(
                    target.id,
                    target.username,
                    target.first_name
                )

                await message.answer(
                    f"пиздюк отвесил щелбан {mention}"
                )
                return

            # Если щелбан отправлен с @username
            username = get_mentioned_username(original_text)

            if username:
                await message.answer(
                    f"пиздюк отвесил щелбан @{username}"
                )

            return

        # =====================================
        # 5. ОБЫЧНЫЙ ТРИГГЕР «ПИЗДЮК» / «ПЕЗДЮК»
        # =====================================

        if PIIZDYUK_PATTERN.search(original_text):
            remember_text(original_text)

            await message.reply(
                random.choice(PIIZDYUK_RESPONSES)
            )
            return

        # =====================================
        # 6. ОСТАЛЬНЫЕ ОСКОРБЛЕНИЯ
        # =====================================

        insult_response = find_insult(original_text)

        if insult_response:
            remember_text(original_text)
            await message.reply(insult_response)
            return

        # =====================================
        # 7. СЛУЧАЙНЫЕ СОБЫТИЯ В ГРУППЕ
        # =====================================

        if message.chat.type in ("group", "supergroup"):

            if random.random() < CATCHPHRASE_CHANCE:
                await message.answer(
                    random.choice(CATCHPHRASES)
                )
                return

            if random.random() < GESTURE_CHANCE:
                gesture = random.choice(GESTURES)

                await message.reply(
                    f"<b>{gesture}</b>",
                    parse_mode="HTML"
                )
                return

        # =====================================
        # 8. ПАМЯТЬ — ОБЫЧНЫМ СООБЩЕНИЕМ
        # =====================================

        if original_text:
            memory = get_random_memory()
            remember_text(original_text)

            if memory and random.random() < MEMORY_CHANCE:
                await message.answer(memory)
                return

        # =====================================
        # 9. ХУЕНИМЫ — ОТВЕТОМ
        # =====================================

        if not original_text:
            return

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

        if random.random() >= HUENIM_CHANCE:
            return

        response = make_huenim(clean_text)

        if response.lower() != clean_text.lower():
            await message.reply(response)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
