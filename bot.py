import os
import html
import threading
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


TOKEN = os.environ.get("BOT_TOKEN")

OWNER = "@teqwyz"

PORT = int(os.environ.get("PORT", 10000))


# =========================
# FLASK
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram Search Bot is alive"



def run_flask():

    app.run(
        host="0.0.0.0",
        port=PORT
    )



# =========================
# SEARCH
# =========================

def search_web(query):

    try:

        r = requests.get(
            "https://html.duckduckgo.com/html/",
            params={
                "q": query
            },
            headers={
                "User-Agent":
                "Mozilla/5.0"
            },
            timeout=15
        )


        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )


        results = []


        for item in soup.select(".result"):

            a = item.select_one(
                ".result__a"
            )


            if a:

                results.append(
                    {
                        "title":
                        a.get_text(
                            " ",
                            strip=True
                        ),

                        "url":
                        a.get("href")
                    }
                )


        return results[:5]


    except Exception as e:

        print(
            "SEARCH ERROR:",
            e
        )

        return []



# =========================
# COMMANDS
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Напиши запрос для поиска."
    )



async def creator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        f"🤖 Меня создал {OWNER}"
    )



# =========================
# MESSAGE
# =========================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()


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



    context.user_data["query"] = text


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
        "Что искать?",
        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )
    )



# =========================
# BUTTONS
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    text = context.user_data.get(
        "query",
        ""
    )


    q = text.replace(
        " ",
        "+"
    )



    if query.data == "music":


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


        await query.edit_message_text(
            "🎵 Музыка:",
            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )
        )



    elif query.data == "video":


        keyboard = [

            [
                Inline
