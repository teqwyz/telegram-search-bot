import os
import html
import asyncio
import threading
import requests

from urllib.parse import quote

from flask import Flask, request

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
    ContextTypes,
    filters
)


# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

PORT = int(
    os.environ.get(
        "PORT",
        10000
    )
)

RENDER_URL = (
    "https://telegram-search-bot-g9vr.onrender.com"
)


# =========================
# FLASK
# =========================

app = Flask(__name__)

telegram_app = None


@app.route("/")
def home():

    return (
        "Telegram Search Bot is running!"
    )



@app.route(
    f"/{BOT_TOKEN}",
    methods=["POST"]
)
def telegram_webhook():

    try:

        data = request.get_json(
            force=True
        )

        update = Update.de_json(
            data,
            telegram_app.bot
        )


        asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update),
            telegram_loop
        )


    except Exception as e:

        print(
            "Webhook error:",
            e
        )


    return "OK"



# =========================
# SEARCH
# =========================

def search_web(query):

    results = []

    encoded = quote(query)


    # -------- GOOGLE --------

    try:

        response = requests.get(
            "https://www.google.com/search",
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
            response.text,
            "html.parser"
        )


        for link in soup.find_all("a"):

            href = link.get(
                "href"
            )


            if (
                href
                and href.startswith(
                    "http"
                )
            ):

                title = link.get_text(
                    " ",
                    strip=True
                )


                if len(title) > 5:

                    results.append(
                        {
                            "title":
                            title[:70],

                            "url":
                            href,

                            "type":
                            "🌐"
                        }
                    )


            if len(results) >= 5:
                break



    except Exception as e:

        print(
            "Google search error:",
            e
        )



    # -------- MUSIC --------


    results.append(
        {
            "title":
            f"Яндекс Музыка — {query}",

            "url":
            (
                "https://music.yandex.ru/search?"
                f"text={encoded}"
            ),

            "type":
            "🎵"
        }
    )



    results.append(
        {
            "title":
            f"VK Музыка — {query}",

            "url":
            (
                "https://vk.com/audios?"
                f"q={encoded}"
            ),

            "type":
            "🎵"
        }
    )



    # -------- VIDEO --------


    results.append(
        {
            "title":
            f"YouTube — {query}",

            "url":
            (
                "https://youtube.com/results?"
                f"search_query={encoded}"
            ),

            "type":
            "🎬"
        }
    )


    return results




# =========================
# COMMANDS
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я поисковый бот 🔎\n\n"
        "Ищу сайты, музыку и видео.\n\n"
        "Просто отправь запрос."
    )



async def creator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "Меня создал @teqwyz)))"
    )



# =========================
# MESSAGES
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



    loading = await update.message.reply_text(
        "🔎 Ищу..."
    )



    results = search_web(
        text
    )



    if not results:

        await loading.edit_text(
            "😕 Ничего не найдено"
        )

        return



    answer = (
        "🔎 <b>Результаты:</b>\n\n"
    )


    buttons = []



    for number, item in enumerate(
        results,
        1
    ):

        title = html.escape(
            item["title"]
        )


        answer += (
            f"{number}. "
            f"{item['type']} "
            f"{title}\n\n"
        )


        buttons.append(
            [
                InlineKeyboardButton(
                    f"Открыть {number}",
                    url=item["url"]
                )
            ]
        )



    await loading.edit_text(
        answer,
        parse_mode="HTML",
        reply_markup=
        InlineKeyboardMarkup(buttons)
    )



# =========================
# TELEGRAM INIT
# =========================

telegram_loop = None


async def setup_bot():

    global telegram_app


    telegram_app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    telegram_app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    telegram_app.add_handler(
        MessageHandler(
            filters.TEXT &
            ~filters.COMMAND,
            message_handler
        )
    )


    await telegram_app.initialize()


    await telegram_app.bot.delete_webhook()



    await telegram_app.bot.set_webhook(
        f"{RENDER_URL}/{BOT_TOKEN}"
    )


    await telegram_app.start()



def telegram_thread():

    global telegram_loop


    telegram_loop = asyncio.new_event_loop()

    asyncio.set_event_loop(
        telegram_loop
    )


    telegram_loop.run_until_complete(
        setup_bot()
    )


    telegram_loop.run_forever()



# =========================
# RUN
# =========================

if __name__ == "__main__":


    thread = threading.Thread(
        target=telegram_thread,
        daemon=True
    )

    thread.start()



    app.run(
        host="0.0.0.0",
        port=PORT
    )
