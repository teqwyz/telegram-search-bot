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


# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "Не найдена переменная BOT_TOKEN"
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
# ПОИСК DUCKDUCKGO
# =========================

def search_duckduckgo(query):

    url = "https://html.duckduckgo.com/html/"


    headers = {
        "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64)"
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


    except Exception as e:

        print(
            "Ошибка DuckDuckGo:",
            e
        )

        return []


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    results = []


    items = soup.select(
        ".result"
    )


    for item in items[:5]:

        link = item.select_one(
            ".result__a"
        )


        if not link:
            continue


        title = link.get_text(
            " ",
            strip=True
        )


        url = link.get(
            "href"
        )


        desc = item.select_one(
            ".result__snippet"
        )


        description = ""

        if desc:

            description = desc.get_text(
                " ",
                strip=True
            )


        results.append(
            {
                "title": title,
                "url": url,
                "description": description
            }
        )


    print(
        "Найдено:",
        len(results)
    )


    return results



# =========================
# TELEGRAM COMMANDS
# =========================

async def start(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я бот поиска информации.\n\n"
        "Напиши любой запрос:\n\n"
        "🔎 Новости ИИ\n"
        "🔎 GTA 6 дата выхода\n"
        "🔎 Кто такой Павел Дуров"
    )



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


    results = search_duckduckgo(
        query
    )


    if not results:

        await msg.edit_text(
            "😕 Ничего не найдено.\n\n"
            "Попробуй изменить запрос."
        )

        return



    text = (
        "🔎 <b>Результаты поиска</b>\n\n"
    )


    for i, item in enumerate(
        results,
        start=1
    ):


        title = (
            item["title"]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


        desc = (
            item["description"]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


        url = item["url"]


        text += (
            f"<b>{i}. {title}</b>\n"
        )


        if desc:

            text += (
                f"{desc}\n"
            )


        text += (
            f'🔗 <a href="{url}">Открыть</a>\n\n'
        )



    await msg.edit_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )



# =========================
# ЗАПУСК БОТА
# =========================

def main():


    threading.Thread(
        target=run_web_server,
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
        "🤖 Бот запущен!"
    )


    bot.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":
    main()
