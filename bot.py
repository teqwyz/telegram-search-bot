import os
import threading
import html
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
    ContextTypes,
    filters,
)


BOT_TOKEN = os.environ["BOT_TOKEN"]

OWNER_USERNAME = "@teqwyz"


# =========================
# FLASK ДЛЯ RENDER
# =========================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Telegram Search Bot is running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))

    web_app.run(
        host="0.0.0.0",
        port=port
    )


# =========================
# ПОИСК
# =========================

def search_web(query):

    url = "https://html.duckduckgo.com/html/"

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    try:

        r = requests.get(
            url,
            params={
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


        for item in soup.select(".result"):

            title = item.select_one(
                ".result__a"
            )

            if not title:
                continue


            link = title.get("href")


            text = title.get_text(
                " ",
                strip=True
            )


            results.append(
                {
                    "title": text,
                    "url": link
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
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я поисковый бот.\n\n"
        "Отправь запрос:\n"
        "🔎 GTA 6 дата выхода\n"
        "🎵 музыка Цоя\n"
        "🎬 трейлер фильма"
    )



# =========================
# СОЗДАТЕЛЬ
# =========================

async def creator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        f"🤖 Меня создал {OWNER_USERNAME}"
    )



# =========================
# ПОИСК В TELEGRAM
# =========================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()


    if (
        "кто твой создатель" in query.lower()
        or
        "кто тебя создал" in query.lower()
    ):

        await creator(
            update,
            context
        )

        return



    msg = await update.message.reply_text(
        "🔎 Ищу..."
    )


    results = search_web(query)


    if not results:

        await msg.edit_text(
            "😕 Ничего не найдено.\n"
            "Попробуй другой запрос."
        )

        return



    text = (
        "🔎 <b>Результаты:</b>\n\n"
    )


    buttons = []


    for i, item in enumerate(
        results,
        1
    ):

        title = html.escape(
            item["title"]
        )


        url = item["url"]


        text += (
            f"{i}. {title}\n"
        )


        buttons.append(
            [
                InlineKeyboardButton(
                    f"🔗 {i}. Открыть",
                    url=url
                )
            ]
        )


    await msg.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )



# =========================
# ЗАПУСК
# =========================

def main():

    threading.Thread(
        target=run_web,
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
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search
        )
    )


    print(
        "🤖 Bot started"
    )


    bot.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":

    main()
