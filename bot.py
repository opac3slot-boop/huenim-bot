import asyncio
import os
import random
import re

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

CHANCE = 0.35

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
            result = "ху" + mapped_vowel + lower_word[first_vowel_idx + 1 :]

    if original.isupper() and len(original) > 1:
        return result.upper()
    if original[0].isupper():
        return result.capitalize()

    return result


async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не задан")

    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(F.text)
    async def handle_message(message: Message):
        if message.from_user and message.from_user.is_bot:
            return

        text = re.sub(r"^[^\wА-Яа-яЁё]+|[^\wА-Яа-яЁё]+$", "", message.text.strip())

        if not re.fullmatch(r"[А-Яа-яЁё]+(-[А-Яа-яЁё]+)*", text):
            return

        if len(text) < 4:
            return

        if random.random() > CHANCE:
            return

        response = make_huenim(text)

        if response.lower() != text.lower():
            await message.reply(response)

    print("Хуеним-бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
