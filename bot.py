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


# =========================
# CONFIG
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

PORT = int(
    os.environ.get(
        "PORT",
        10000
    )
)

OWNER = "@teqwyz"


# =========================
# FLASK FOR RENDER
# =========================

app = Flask(__name__)


@app.route("/")
def index():
    return "Bot is running!"



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
            timeout=10
        )


        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )


        results = []


        for item in soup.select(
            ".result"
        ):

            a = item.select_one(
                ".result__a"
            )


            if a:

                results.append(
                    (
                        a.text.strip(),
                        a.get("href")
                    )
                )


        return results[:5]


    except Exception as e:

        print(
            "SEARCH ERROR:",
            e
        )

        return []



# =========================
# LINKS
# =========================

def encode(text):

    return requests.utils.quote(
        text
    )



def music_buttons(query):

    q = encode(query)

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
                    url=f"https://vk.com/search?c%5Bq%5D={q}&c%5Bsection%5D=audio"
                )
            ]

        ]
    )



def video_buttons(query):

    q = encode(query)

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "▶ YouTube",
                    url=f"https://youtube.com/results?search_query={q}"
                )
            ]

        ]
    )



def menu_buttons():

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "🌐 Веб-поиск",
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
            ]

        ]
    )



# =========================
# TELEGRAM
# =========================

user_mode = {}



async def start(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я поисковый бот.\n"
        "Выбери режим поиска:",
        reply_markup=menu_buttons()
    )



async def creator(
        update,
        context
):

    await update.message.reply_text(
        f"🤖 Меня создал {OWNER}"
    )



async def button(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    user_mode[
        query.from_user.id
    ] = query.data


    names = {

        "web":
        "🌐 Веб-поиск",

        "music":
        "🎵 Музыка",

        "video":
        "🎬 Видео"

    }


    await query.edit_message_text(

        "Выбран режим:\n"
        + names.get(
            query.data,
            "Поиск"
        )
        +
        "\n\nОтправь запрос."

    )



async def message(
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



    mode = user_mode.get(
        update.message.from_user.id,
        "web"
    )


    if mode == "music":

        await update.message.reply_text(
            "Выбери сервис:",
            reply_markup=
            music_buttons(text)
        )

        return



    if mode == "video":

        await update.message.reply_text(
            "Видео:",
            reply_markup=
            video_buttons(text)
        )

        return



    msg = await update.message.reply_text(
        "🔎 Ищу..."
    )


    results = search_web(
        text
    )


    if not results:

        await msg.edit_text(
            "😕 Ничего не найдено"
        )

        return



    answer = (
        "🌐 <b>Результаты:</b>\n\n"
    )


    buttons = []


    for i, item in enumerate(
        results,
        1
    ):

        title = html.escape(
            item[0]
        )


        answer += (
            f"{i}. {title}\n\n"
        )


        buttons.append(
            [

                InlineKeyboardButton(
                    f"🔗 {i}",
                    url=item[1]
                )

            ]
        )


    await msg.edit_text(

        answer,

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup(
            buttons
        )

    )



# =========================
# MAIN
# =========================


def main():

    flask_thread = threading.Thread(
        target=run_flask
    )

    flask_thread.daemon = True

    flask_thread.start()



    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    application.add_handler(
        CallbackQueryHandler(
            button
        )
    )


    application.add_handler(
        MessageHandler(
            filters.TEXT
            &
            ~filters.COMMAND,
            message
        )
    )


    print(
        "BOT STARTED"
    )


    application.run_polling()



if __name__ == "__main__":

    main()
