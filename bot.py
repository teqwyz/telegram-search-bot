import os
import html
import threading
import requests

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


BOT_TOKEN = os.environ["BOT_TOKEN"]

OWNER_USERNAME = "@teqwyz"

PORT = int(os.environ.get("PORT", 10000))

RENDER_URL = "https://telegram-search-bot-g9vr.onrender.com"


# =========================
# FLASK
# =========================

app = Flask(__name__)

telegram_app = None


@app.route("/")
def home():
    return "Telegram Search Bot is running!"



@app.route(
    f"/{BOT_TOKEN}",
    methods=["POST"]
)
def webhook():

    data = request.get_json(force=True)

    update = Update.de_json(
        data,
        telegram_app.bot
    )

    import asyncio

    asyncio.run(
        telegram_app.process_update(update)
    )

    return "OK"



# =========================
# SEARCH
# =========================

def search_web(query):

    url = "https://lite.duckduckgo.com/lite/"

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }


    try:

        r = requests.post(
            url,
            data={
                "q": query
            },
            headers=headers,
            timeout=20
        )


        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )


        results = []


        for link in soup.find_all(
            "a"
        ):

            href = link.get("href")

            title = link.text.strip()


            if (
                href
                and
                href.startswith("http")
                and title
            ):

                results.append(
                    {
                        "title": title,
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



# =========================
# COMMANDS
# =========================


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я поисковый бот.\n\n"
        "Отправь запрос и я найду ссылки."
    )



async def creator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        f"🤖 Меня создал {OWNER_USERNAME}"
    )



# =========================
# MESSAGE
# =========================


async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()


    if not text:
        return



    if any(
        word in text.lower()
        for word in [
            "кто твой создатель",
            "кто тебя создал",
            "кто автор"
        ]
    ):

        await creator(
            update,
            context
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
            "😕 Ничего не найдено.\n"
            "Попробуй изменить запрос."
        )

        return



    buttons = []

    answer = (
        "🔎 <b>Результаты:</b>\n\n"
    )


    for i, item in enumerate(
        results,
        1
    ):

        title = html.escape(
            item["title"]
        )


        answer += (
            f"{i}. {title}\n\n"
        )


        buttons.append(
            [
                InlineKeyboardButton(
                    f"🔗 Открыть {i}",
                    url=item["url"]
                )
            ]
        )


    await msg.edit_text(
        answer,
        parse_mode="HTML",
        reply_markup=
        InlineKeyboardMarkup(buttons)
    )



# =========================
# START BOT
# =========================


async def init_bot():

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
        CommandHandler(
            "creator",
            creator
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



def run():

    import asyncio


    asyncio.run(
        init_bot()
    )


    app.run(
        host="0.0.0.0",
        port=PORT
    )



if __name__ == "__main__":
    run()
