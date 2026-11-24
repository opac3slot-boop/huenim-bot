
import asyncio
import random
import re
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

CHANCE = 0.35

SPECIAL_WORDS = {
    "лестница": "хуестница",
    "яблоко": "хуяблоко",
    "ялта": "хуялта",
    "математика": "хуематика",
    "кошка": "хуёшка",
    "гипсокартон": "хуипсокартон",
    "пылесос": "хуесос",
    "крокодил": "хуедил",
    "пылесборник": "хуесборник",
    "самокат": "хуекат",
    "понедельник": "хуедельник",
    "бутерброд": "хуерброд",
    "электричка": "хуетричка",
    "бегемот": "хуемот",
    "мандарин": "хуерин",
    "аккордеон": "хуердеон",
    "паровоз": "хуевоз",
    "аптека": "хуетека",
}


def make_huenim(word):
    original = word
    word = word.lower()

    result = SPECIAL_WORDS.get(word)

    if result is None:
        result = "ху" + word

    if original[0].isupper():
        result = result.capitalize()

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

        text = message.text.strip()

        if not re.fullmatch(r"[А-Яа-яЁё-]+", text):
            return

        if len(text) < 3:
            return

        if random.random() > CHANCE:
            return

        await message.reply(make_huenim(text))

    print("Хуеним-бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
