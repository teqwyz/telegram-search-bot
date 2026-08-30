import os
import html
import asyncio
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
async def webhook():

    update = Update.de_json(
        request.get_json(force=True),
        telegram_app.bot
    )

    await telegram_app.process_update(update)

    return "OK"



# =========================
# SEARCH
# =========================

def search_web(query):

    try:

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={
                "q": query
            },
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=20
        )


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        results = []


        for item in soup.select(".result"):

            link = item.select_one(
                ".result__a"
            )


            if link:

                results.append(
                    {
                        "title":
                        link.get_text(
                            " ",
                            strip=True
                        ),

                        "url":
                        link.get("href")
                    }
                )


        return results[:5]


    except Exception as e:

        print(
            "Search error:",
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
        "Я поисковый бот.\n"
        "Отправь запрос 🔎"
    )



async def creator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        f"🤖 Меня создал {OWNER_USERNAME}"
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
        "кто твой создатель" in text.lower()
        or
        "кто тебя создал" in text.lower()
    ):

        await creator(
            update,
            context
        )

        return



    msg = await update.message.reply_text(
        "🔎 Ищу..."
    )


    results = search_web(text)


    if not results:

        await msg.edit_text(
            "😕 Ничего не найдено"
        )

        return



    buttons = []

    answer = (
        "🔎 <b>Результаты:</b>\n\n"
    )


    for i, item in enumerate(results, 1):

        title = html.escape(
            item["title"]
        )


        answer += (
            f"{i}. {title}\n"
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
        reply_markup=InlineKeyboardMarkup(buttons)
    )



# =========================
# TELEGRAM INIT
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


    print("Telegram bot started")



def start_async_loop():

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    loop.run_until_complete(
        init_bot()
    )

    loop.run_forever()



# =========================
# RUN
# =========================

if __name__ == "__main__":

    thread = threading.Thread(
        target=start_async_loop,
        daemon=True
    )

    thread.start()


    app.run(
        host="0.0.0.0",
        port=PORT
    )
