import os
import html
import threading
import asyncio
import requests

from flask import Flask
from bs4 import BeautifulSoup

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)


TOKEN = os.environ["BOT_TOKEN"]

OWNER = "@teqwyz"

PORT = int(
    os.environ.get(
        "PORT",
        10000
    )
)


# ==========================
# FLASK
# ==========================

app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram Search Bot is running"



def run_flask():

    app.run(
        host="0.0.0.0",
        port=PORT
    )



# ==========================
# WEB SEARCH
# ==========================


def web_search(text):

    try:

        response = requests.get(
            "https://www.google.com/search",
            params={
                "q": text
            },
            headers={
                "User-Agent":
                "Mozilla/5.0"
            },
            timeout=10
        )


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        results = []


        for link in soup.find_all("a"):

            href = link.get("href")

            title = link.text.strip()


            if (
                href
                and href.startswith("http")
                and len(title) > 5
            ):

                results.append(
                    {
                        "title": title[:80],
                        "url": href
                    }
                )


        return results[:5]


    except Exception as e:

        print(
            "SEARCH ERROR:",
            e
        )

        return []



# ==========================
# COMMANDS
# ==========================


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я поисковый бот.\n\n"
        "Напиши что найти:"
    )



async def creator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        f"🤖 Меня создал {OWNER}"
    )



# ==========================
# TEXT SEARCH
# ==========================


async def search_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()


    if not text:
        return


    if (
        "кто тебя создал"
        in text.lower()
        or
        "кто твой создатель"
        in text.lower()
    ):

        await creator(
            update,
            context
        )

        return



    context.user_data["search"] = text


    keyboard = [

        [
            InlineKeyboardButton(
                "🎵 Музыка",
                callback_data="music"
            )
        ],

        [
            InlineKeyboardButton(
                "▶️ Видео",
                callback_data="video"
            )
        ],

        [
            InlineKeyboardButton(
                "🔎 Веб-поиск",
                callback_data="web"
            )
        ]

    ]


    await update.message.reply_text(
        "Выберите тип поиска:",
        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )
    )



# ==========================
# BUTTONS
# ==========================


async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    callback = update.callback_query

    await callback.answer()


    text = context.user_data.get(
        "search",
        ""
    )


    q = text.replace(
        " ",
        "+"
    )


    # MUSIC

    if callback.data == "music":


        keyboard = [

            [
                InlineKeyboardButton(
                    "🎧 Spotify",
                    url=
                    f"https://open.spotify.com/search/{q}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎵 Яндекс Музыка",
                    url=
                    f"https://music.yandex.ru/search?text={q}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎶 VK Музыка",
                    url=
                    f"https://vk.com/audios?q={q}"
                )
            ]

        ]


        await callback.edit_message_text(

            "🎵 Музыкальный поиск:",

            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )

        )



    # VIDEO

    elif callback.data == "video":


        keyboard = [

            [

                InlineKeyboardButton(
                    "▶️ YouTube",
                    url=
                    f"https://www.youtube.com/results?search_query={q}"
                )

            ]

        ]


        await callback.edit_message_text(

            "▶️ Видео поиск:",

            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )

        )



    # WEB

    elif callback.data == "web":


        results = web_search(text)


        keyboard = []


        answer = (
            "🔎 <b>Результаты:</b>\n\n"
        )


        if not results:

            answer += (
                "Ничего не найдено"
            )


        for i, item in enumerate(
            results,
            1
        ):

            answer += (
                f"{i}. "
                f"{html.escape(item['title'])}\n"
            )


            keyboard.append(

                [

                    InlineKeyboardButton(
                        f"🌐 Открыть {i}",
                        url=item["url"]
                    )

                ]

            )


        await callback.edit_message_text(

            answer,

            parse_mode="HTML",

            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )

        )



# ==========================
# ERROR HANDLER
# ==========================


async def error_handler(
    update,
    context
):

    print(
        "ERROR:",
        context.error
    )



# ==========================
# BOT
# ==========================


async def run_bot():


    bot = (

        Application
        .builder()
        .token(TOKEN)
        .build()

    )


    bot.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    bot.add_handler(
        MessageHandler(
            filters.TEXT &
            ~filters.COMMAND,
            search_handler
        )
    )


    bot.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )


    bot.add_error_handler(
        error_handler
    )


    print(
        "BOT STARTED"
    )


    await bot.run_polling(
        drop_pending_updates=True
    )



# ==========================
# START
# ==========================


if __name__ == "__main__":


    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()


    asyncio.run(
        run_bot()
    )
