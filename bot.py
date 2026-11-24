
import asyncio
import random
import re
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

TOKEN = os.getenv("BOT_TOKEN")
CHANCE = 0.20

bot = Bot(token=TOKEN)
dp = Dispatcher()

VOWELS = "аеёиоуыэюя"


def make_huenim(word):
    word = word.lower()
    variants = ["ху" + word]

    vowels = [i for i, c in enumerate(word) if c in VOWELS]

    if len(vowels) >= 2:
        variants.append("ху" + word[vowels[1]:])

    if vowels:
        pos = vowels[0]
        if pos + 2 < len(word):
            variants.append("ху" + word[pos + 2:])

    if len(word) >= 3:
        variants.append(word[0] + "ху" + word[1:])

    variants = list(set(v for v in variants if len(v) >= 3 and v != word))
    result = random.choice(variants)

    return result.capitalize() if word[0].isupper() else result


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


async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")

    print("Хуеним-бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
