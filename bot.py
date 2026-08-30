import os
import threading
import requests
from bs4 import BeautifulSoup

from flask import Flask

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


BOT_TOKEN = os.environ.get("BOT_TOKEN")


# =====================
# FLASK SERVER
# =====================

app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram Search Bot is running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )


# =====================
# SEARCH
# =====================

def duck_search(query):

    url = "https://lite.duckduckgo.com/lite/"

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    try:

        response = requests.post(
            url,
            data={
                "q": query
            },
            headers=headers,
            timeout=20
        )

        response.raise_for_status()


    except Exception as e:

        print(
            "Search error:",
            e
        )

        return []


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
            and title
        ):

            results.append(
                {
                    "title": title,
                    "url": href
                }
            )


    return results[:5]



# =====================
# COMMAND START
# =====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я поисковый бот.\n\n"
        "Напиши запрос, например:\n\n"
        "🔎 GTA 6 дата выхода\n"
        "🔎 Новости ИИ\n"
        "🔎 Кто такой Дуров"
    )



# =====================
# SEARCH HANDLER
# =====================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()


    if not query:
        return


    msg = await update.message.reply_text(
        "🔎 Ищу..."
    )


    results = duck_search(query)


    if not results:

        await msg.edit_text(
            "😕 Ничего не найдено.\n"
            "Попробуй изменить запрос."
        )

        return



    text = (
        "🔎 <b>Результаты:</b>\n\n"
    )


    for i, item in enumerate(
        results,
        start=1
    ):

        title = (
            item["title"]
            .replace("&","&amp;")
            .replace("<","&lt;")
            .replace(">","&gt;")
        )


        url = item["url"]


        text += (
            f"{i}. <b>{title}</b>\n"
            f"🔗 <a href=\"{url}\">Открыть</a>\n\n"
        )


    await msg.edit_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=False
    )



# =====================
# MAIN
# =====================

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
        "BOT STARTED"
    )


    bot.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":

    main()
