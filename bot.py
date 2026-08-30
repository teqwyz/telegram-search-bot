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

BOT_TOKEN = os.environ["BOT_TOKEN"]

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Telegram Search Bot is running!"


# =========================
# ПОИСК DUCKDUCKGO
# =========================

def search_duckduckgo(query):
    url = "https://html.duckduckgo.com/html/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }

    try:
        response = requests.get(
            url,
            params={"q": query},
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print("Ошибка подключения к DuckDuckGo:", repr(error))
        return []


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    results = []


    for item in soup.select(".result"):

        link = item.select_one(".result__a")

        if not link:
            continue


        title = link.get_text(
            " ",
            strip=True
        )

        result_url = link.get("href")


        description_element = item.select_one(
            ".result__snippet"
        )

        description = ""

        if description_element:
            description = description_element.get_text(
                " ",
                strip=True
            )


        if title and result_url:

            results.append({
                "title": title,
                "url": result_url,
                "description": description,
            })


    print(
        f"DuckDuckGo: найдено {len(results)} результатов"
    )

    return results


# =========================
# /START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я бот для поиска информации в интернете.\n\n"
        "Просто отправь мне запрос:\n\n"
        "🔎 Новости технологий\n"
        "🔎 Кто такой Павел Дуров\n"
        "🔎 Дата выхода GTA 6"
    )


# =========================
# ПОИСК
# =========================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()

    if not query:
        return


    message = await update.message.reply_text(
        f"🔎 Ищу:\n{query}"
    )


    try:

        results = search_duckduckgo(query)


        if not results:

            await message.edit_text(
                "😕 DuckDuckGo не вернул результаты.\n\n"
                "Попробуй немного изменить запрос."
            )

            return


        text = "🔎 <b>Результаты поиска</b>\n\n"


        for i, result in enumerate(
            results[:5],
            1
        ):

            title = result["title"]
            description = result["description"]
            url = result["url"]


            # Защита от символов HTML
            title = (
                title
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )


            description = (
                description
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
                f'🔗 <a href="{url}">Открыть</a>\n\n'
            )


        await message.edit_text(
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )


    except Exception as error:

        print(
            "Ошибка обработки поиска:",
            repr(error)
        )


        await message.edit_text(
            "❌ При поиске произошла ошибка."
        )


# =========================
# FLASK
# =========================

def run_web_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )


    web_app.run(
        host="0.0.0.0",
        port=port,
    )


# =========================
# ЗАПУСК
# =========================

def main():

    threading.Thread(
        target=run_web_server,
        daemon=True,
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


    print("🤖 Бот запущен!")


    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
