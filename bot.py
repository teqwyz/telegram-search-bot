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


# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

OWNER_USERNAME = "@teqwyz"

PORT = int(os.environ.get("PORT", 10000))

WEBHOOK_URL = (
    "https://telegram-search-bot-g9vr.onrender.com/"
    + BOT_TOKEN
)


# =========================
# FLASK
# =========================

app = Flask(__name__)

telegram_app = None

event_loop = None



@app.route("/")
def home():

    return "Telegram Search Bot is running!"



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
            event_loop
        )


        return "OK"


    except Exception as e:

        print(
            "Webhook error:",
            e
        )

        return "ERROR"



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
                "User-Agent":
                "Mozilla/5.0"
            },
            timeout=15
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


            if not link:
                continue


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
        "Я поисковый бот 🔎\n\n"
        "Напиши запрос — я найду информацию."
    )



async def creator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        f"🤖 Меня создал {OWNER_USERNAME}"
    )



# =========================
# TEXT
# =========================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    text = update.message.text.strip()



    if (
        "кто твой создатель"
        in text.lower()

        or

        "кто тебя создал"
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
        "🔎 <b>Результаты поиска:</b>\n\n"
    )


    buttons = []


    for i, item in enumerate(
        results,
        1
    ):


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



    await loading.edit_text(
        answer,
        parse_mode="HTML",
        reply_markup=
        InlineKeyboardMarkup(buttons)
    )



# =========================
# TELEGRAM START
# =========================

async def telegram_start():


    global telegram_app
    global event_loop


    event_loop = asyncio.get_running_loop()


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


    await telegram_app.bot.delete_webhook(
        drop_pending_updates=True
    )


    await telegram_app.bot.set_webhook(
        WEBHOOK_URL
    )


    await telegram_app.start()


    print(
        "✅ Telegram bot started"
    )



def telegram_thread():


    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(
        loop
    )


    loop.run_until_complete(
        telegram_start()
    )


    loop.run_forever()



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
