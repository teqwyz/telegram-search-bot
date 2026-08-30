import os
import html
import requests
import threading
import asyncio

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


BOT_TOKEN = os.environ.get("BOT_TOKEN")

PORT = int(os.environ.get("PORT", 10000))

RENDER_URL = "https://telegram-search-bot-g9vr.onrender.com"


app = Flask(__name__)

telegram_app = None


# =====================
# FLASK
# =====================


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

    asyncio.run(
        telegram_app.process_update(update)
    )

    return "OK"



# =====================
# SEARCH
# =====================


def search_web(query):

    try:

        url = "https://www.google.com/search"

        headers = {
            "User-Agent":
            "Mozilla/5.0"
        }


        r = requests.get(
            url,
            params={
                "q": query
            },
            headers=headers,
            timeout=10
        )


        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )


        results = []


        for a in soup.find_all("a"):

            href = a.get("href")


            if (
                href
                and href.startswith("http")
            ):

                title = a.get_text(
                    " ",
                    strip=True
                )


                if len(title) > 5:

                    results.append(
                        {
                            "title": title,
                            "url": href
                        }
                    )


            if len(results) >= 5:
                break



        return results


    except Exception as e:

        print(
            "SEARCH ERROR:",
            e
        )

        return []



# =====================
# COMMANDS
# =====================


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я поисковый Telegram-бот.\n"
        "Отправь мне запрос 🔎"
    )



async def creator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🤖 Меня создал @teqwyz"
    )



# =====================
# MESSAGE
# =====================


async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text


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



    msg = await update.message.reply_text(
        "🔎 Ищу информацию..."
    )


    results = search_web(text)



    if not results:

        await msg.edit_text(
            "😕 Не смог найти результаты"
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
            item["title"][:70]
        )


        answer += (
            f"{i}. {title}\n\n"
        )


        buttons.append(
            [
                InlineKeyboardButton(
                    f"Открыть {i}",
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



# =====================
# TELEGRAM START
# =====================


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



def start_bot():

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    loop.run_until_complete(
        init_bot()
    )

    loop.run_forever()



# =====================
# RUN
# =====================


if __name__ == "__main__":

    threading.Thread(
        target=start_bot,
        daemon=True
    ).start()


    app.run(
        host="0.0.0.0",
        port=PORT
    )
