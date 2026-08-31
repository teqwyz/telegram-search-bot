import os
import html
import threading
import requests

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)


BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

OWNER = "@teqwyz"

app = Flask(__name__)

modes = {}


# =====================
# FLASK
# =====================

@app.route("/")
def home():
    return "Telegram Search Bot is running!"


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT
    )


# =====================
# SEARCH
# =====================

def encode(text):
    return requests.utils.quote(
        text,
        safe=""
    )


def web_search(query):

    results = []

    try:

        r = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1
            },
            timeout=10
        )

        data = r.json()


        if data.get("AbstractText"):

            results.append(
                (
                    data["Heading"],
                    data["AbstractURL"]
                )
            )


        for item in data.get(
            "RelatedTopics",
            []
        ):

            if isinstance(item, dict):

                if item.get("Text") and item.get("FirstURL"):

                    results.append(
                        (
                            item["Text"],
                            item["FirstURL"]
                        )
                    )


        if results:
            return results[:5]


    except Exception as e:
        print(
            "SEARCH ERROR:",
            e
        )


    # запасной вариант

    return [
        (
            "🔎 Открыть поиск Google",
            f"https://www.google.com/search?q={encode(query)}"
        )
    ]



# =====================
# BUTTONS
# =====================

def main_menu():

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "🌐 Веб",
                    callback_data="web"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎵 Музыка",
                    callback_data="music"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎬 Видео",
                    callback_data="video"
                )
            ],

            [
                InlineKeyboardButton(
                    "📰 Новости",
                    callback_data="news"
                )
            ],

            [
                InlineKeyboardButton(
                    "📚 Википедия",
                    callback_data="wiki"
                )
            ]

        ]
    )



def music_menu(text):

    q = encode(text)

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "🎵 Spotify",
                    url=f"https://open.spotify.com/search/{q}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎵 Яндекс Музыка",
                    url=f"https://music.yandex.ru/search?text={q}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎵 VK Музыка",
                    url=f"https://vk.com/search?c%5Bsection%5D=audio&c%5Bq%5D={q}"
                )
            ]

        ]
    )



def video_menu(text):

    q = encode(text)

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "▶ YouTube",
                    url=f"https://www.youtube.com/results?search_query={q}"
                )
            ]

        ]
    )



# =====================
# TELEGRAM
# =====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Выбери поиск:",
        reply_markup=main_menu()
    )



async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    modes[
        query.from_user.id
    ] = query.data


    await query.edit_message_text(
        "✅ Режим выбран.\n"
        "Отправь запрос."
    )



async def message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    user = update.message.from_user.id


    if "кто тебя создал" in text.lower():

        await update.message.reply_text(
            f"🤖 Меня создал {OWNER}"
        )

        return



    mode = modes.get(
        user,
        "web"
    )


    if mode == "music":

        await update.message.reply_text(
            "🎵 Музыка:",
            reply_markup=music_menu(text)
        )

        return



    if mode == "video":

        await update.message.reply_text(
            "🎬 Видео:",
            reply_markup=video_menu(text)
        )

        return



    if mode == "news":

        await update.message.reply_text(

            "📰 Новости:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Google News",
                            url=f"https://news.google.com/search?q={encode(text)}"
                        )
                    ]
                ]
            )

        )

        return



    if mode == "wiki":

        await update.message.reply_text(

            "📚 Википедия:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Открыть",
                            url=f"https://ru.wikipedia.org/wiki/{encode(text)}"
                        )
                    ]
                ]
            )

        )

        return



    msg = await update.message.reply_text(
        "🔎 Ищу..."
    )


    results = web_search(text)



    answer = "🌐 Результаты:\n\n"

    keyboard = []


    for i, item in enumerate(
        results,
        1
    ):

        title, url = item


        answer += (
            f"{i}. {html.escape(title[:100])}\n"
        )


        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🔗 {i}",
                    url=url
                )
            ]
        )


    await msg.edit_text(
        answer,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )



# =====================
# START
# =====================

def run():

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()


    bot = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    bot.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    bot.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )


    bot.add_handler(
        MessageHandler(
            filters.TEXT &
            ~filters.COMMAND,
            message
        )
    )


    print(
        "BOT STARTED"
    )


    bot.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":
    run()
