import os
import threading
import requests

from flask import Flask
from bs4 import BeautifulSoup

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================
# FLASK SERVER
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram Search Bot is running!"


def run_web_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


# =========================
# TOKEN
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN не найден в переменных окружения"
    )


# =========================
# DUCKDUCKGO SEARCH
# =========================

def search_duckduckgo(query):

    url = "https://html.duckduckgo.com/html/"

    headers = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:

        response = requests.get(
            url,
            params={
                "q": query
            },
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

    except Exception as error:

        print(
            "Ошибка DuckDuckGo:",
            error
        )

        return []


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    results = []


    for item in soup.select(".result"):

        title_block = item.select_one(
            ".result__a"
        )

        if not title_block:
            continue


        title = title_block.get_text(
            " ",
            strip=True
        )


        link = title_block.get(
            "href"
        )


        description_block = item.select_one(
            ".result__snippet"
        )


        description = ""

        if description_block:

            description = (
                description_block
                .get_text(
                    " ",
                    strip=True
                )
            )


        results.append(
            {
                "title": title,
                "url": link,
                "description": description
            }
        )


    print(
        f"Найдено результатов: {len(results)}"
    )


    return results



# =========================
# COMMAND /START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я Telegram-бот поиска.\n\n"
        "Отправь любой запрос:\n\n"
        "🔎 Новости ИИ\n"
        "🔎 GTA 6 дата выхода\n"
        "🔎 Кто такой Павел Дуров"
    )



# =========================
# SEARCH HANDLER
# =========================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()


    if not query:
        return


    msg = await update.message.reply_text(
        f"🔎 Ищу:\n{query}"
    )


    try:

        results = search_duckduckgo(
            query
        )


        if not results:

            await msg.edit_text(
                "😕 Ничего не найдено."
            )

            return



        text = (
            "🔎 <b>Результаты поиска:</b>\n\n"
        )


        for i, result in enumerate(
            results[:5],
            1
        ):

            title = (
                result["title"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )


            description = (
                result["description"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )


            text += (
                f"<b>{i}. {title}</b>\n"
            )


            if description:

                text += (
                    f"{description}\n"
                )


            text += (
                f"🔗 {result['url']}\n\n"
            )



        await msg.edit_text(
            text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )


    except Exception as error:

        print(
            "Ошибка поиска:",
            repr(error)
        )


        await msg.edit_text(
            "❌ Ошибка при поиске."
        )



# =========================
# START BOT
# =========================

def main():

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()



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
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search
        )
    )


    print(
        "🤖 Бот запущен!"
    )


    application.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":

    main()
