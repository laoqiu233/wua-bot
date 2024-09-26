import asyncio
import logging
import random
import re
from uuid import uuid4

from aiogram import Bot, Dispatcher, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.formatting import as_section, Bold, as_marked_section, as_line, as_numbered_section, Text, Italic
from aiogram.filters import Filter, Command
from aiogram.types import Message
from pydantic_settings import BaseSettings, SettingsConfigDict

from bot.models import Wua
from bot.postgres import WuaDao, get_async_session

logging.basicConfig()
logging.root.setLevel(logging.INFO)


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=[".env", ".env.secrets"])
    bot_token: str = "hackme"
    db_url: str = "postgresql+asyncpg://wua:wua@localhost/wua"


settings = BotSettings()
wua_router = Router()

def get_author_from_message(message: Message) -> str:
    if message.from_user is None:
        return "анонимус"
    else:
        return message.from_user.username or "анонимус"

class WuaFilter(Filter):
    async def __call__(self, message: Message):
        if message.text is not None:
            matches = re.findall(r"у{1,}а{1,}", message.text, flags=re.IGNORECASE)
            wuas = []
            for match in matches:
                match: str

                author = get_author_from_message(message)
                chat = str(message.chat.id)

                wuas.append(
                    Wua(
                        id=uuid4(),
                        size=len(match),
                        wu_size=match.lower().count("у"),
                        a_size=match.lower().count("а"),
                        author=author,
                        chat=chat,
                    )
                )
            if len(wuas) != 0:
                return {"wuas": wuas}
        return False


wua_messages = [
    "УАААААА",
    "уааааа",
    "Уа.",
    "уаа уаа...",
    "уааа?",
    "УА!",
    "уууууаааааааааааа",
    "уАаАаАаА",
]


@wua_router.message(WuaFilter())
async def wua(message: Message, wuas: list[Wua], wua_dao: WuaDao):
    author = get_author_from_message(message)
    longest_wua = max(wuas, key=lambda wua: wua.size)
    await wua_dao.put_wua(longest_wua)
    chat_wuas = await wua_dao.get_all_wuas_in_chat(str(message.chat.id))
    my_wuas = list(filter(lambda wua: wua.author == author, chat_wuas))
    chat_position = 0
    my_position = 0

    for index, chat_wua in enumerate(chat_wuas):
        if chat_wua.id == longest_wua.id:
            chat_position = index + 1
            break

    for index, my_wua in enumerate(my_wuas):
        if my_wua.id == longest_wua.id:
            my_position = index + 1
            break

    wua_message = random.choice(wua_messages)
    achivements = []

    if chat_position <= 5:
        achivements.append(as_line(
            "Этот уаа занимает ",
            Bold(f"{chat_position} место "),
            "среди всех уаа в этом чате!"
        ))

    if my_position <= 3:
        achivements.append(as_line(
            "Этот уаа занимает ",
            Bold(f"{my_position} место "),
            "среди твоих уаа в этом чате!"
        ))

    await message.reply(as_section(
        Bold(wua_message),
        *achivements
    ).as_markdown())

@wua_router.message(Command("wua_stats"))
async def wua_statistics(message: Message, wua_dao: WuaDao):
    author = get_author_from_message(message)
    all_wuas = await wua_dao.get_all_wuas_in_chat(str(message.chat.id))
    sizes = 0
    wu_percent = 0
    a_percent = 0

    my_top_wua = None

    for wua in all_wuas:
        sizes += wua.size
        wu_percent += wua.wu_size / wua.size
        a_percent += wua.a_size / wua.size

        if my_top_wua is None and wua.author == author:
            my_top_wua = wua 

    mean_size = sizes / len(all_wuas)
    mean_wu_percent = (wu_percent / len(all_wuas)) * 100
    mean_a_precent = (a_percent / len(all_wuas)) * 100
    
    stats = [
        f"Всего УААА было в этом чате: {len(all_wuas)}",
        f"Средний размер УААА в этом чате: {mean_size:.2f}",
        f"Среднее доля У в УААА: {mean_wu_percent:.2f}%",
        f"Средняя доля ААА в УААА: {mean_a_precent:.2f}%"
    ]

    if my_top_wua is not None:
        stats.append(f"Твой самый длинный УААА имеет размер {my_top_wua.size}")

    await message.reply(as_marked_section(
        Bold("УААА статистики этого чата:"),
        *stats
    ).as_markdown())

@wua_router.message(Command("top_wua"))
async def top_wuas(message: Message, wua_dao: WuaDao):
    all_wuas = await wua_dao.get_all_wuas_in_chat(str(message.chat.id))
    
    mean_wua_by_user: dict[str, float] = {}
    wua_count_by_user: dict[str, int] = {}

    for wua in all_wuas:
        mean_wua_by_user[wua.author] = mean_wua_by_user.get(wua.author, 0) + wua.size
        wua_count_by_user[wua.author] = wua_count_by_user.get(wua.author, 0) + 1

    for wua_author in mean_wua_by_user:
        mean_wua_by_user[wua_author] = mean_wua_by_user[wua_author] / wua_count_by_user[wua_author]

    top_users_by_count = sorted(wua_count_by_user.keys(), key=lambda user: wua_count_by_user[user])[:5]
    top_users_by_size = sorted(mean_wua_by_user.keys(), key=lambda user: mean_wua_by_user[user])[:5]

    top_size_lines = []
    top_count_lines = []

    for top_user_by_size in top_users_by_size:
        top_size_lines.append(Text(
            f"{top_user_by_size} - ",
            Italic(f"{mean_wua_by_user[top_user_by_size]:.2f}")
        ))
    for top_user_by_count in top_users_by_count:
        top_count_lines.append(Text(
            f"{top_user_by_count} - ",
            Italic(f"{wua_count_by_user[top_user_by_count]}")
        ))

    await message.reply(as_section(
        Bold(f"УААА рейтинг этого чата"),
        as_line("------"),
        as_line(as_numbered_section(
            f"Топ {len(top_size_lines)} юзеров по среднему размеру УААА:",
            *top_size_lines
        )),
        as_line("------"),
        as_numbered_section(
            f"Топ {len(top_count_lines)} юзеров по количеству УААА",
            *top_count_lines
        )
    ).as_markdown())

async def main():
    async_session = get_async_session(settings.db_url)
    wua_dao = WuaDao(async_session)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(
        parse_mode=ParseMode.MARKDOWN_V2
    ))
    dp = Dispatcher(wua_dao=wua_dao)
    dp.include_router(wua_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
