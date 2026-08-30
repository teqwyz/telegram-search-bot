import os
import threading
import html
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

# УКАЖИ СВОЙ TELEGRAM USERNAME
CREATOR = "@teqwyz"


# =========================
# FLASK ДЛЯ RENDER
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram Search Bot is running!"



def run_web():

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
# ПОИСК
# =========================

def search_web(query):

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


    except Exception as error:

        print(
            "Ошибка поиска:",
            error
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



# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я поисковый Telegram-бот.\n\n"
        "Отправь мне запрос, и я найду информацию 🔎"
    )



# =========================
# CREATOR
# =========================

async def creator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        f"🤖 Меня создал:\n{CREATOR}"
    )



# =========================
# ОБ ИНФОРМАЦИИ
# =========================

async def about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🤖 Telegram Search Bot\n\n"
        "Версия: 1.0\n"
        f"Создатель: {CREATOR}"
    )



# =========================
# ОСНОВНОЙ ОБРАБОТЧИК
# =========================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()

    if not query:
        return


    low = query.lower()


    # Проверка вопроса о создателе

    creator_questions = [

        "кто твой создатель",
        "кто тебя создал",
        "кто твой автор",
        "кто тебя сделал",
        "кто разработчик",
        "кто написал тебя"

    ]


    if any(
        item in low
        for item in creator_questions
    ):

        await update.message.reply_text(
            f"🤖 Меня создал:\n{CREATOR}"
        )

        return



    message = await update.message.reply_text(
        "🔎 Ищу..."
    )


    results = search_web(query)



    if not results:

        await message.edit_text(
            "😕 Ничего не найдено.\n"
            "Попробуй изменить запрос."
        )

        return



    text = (
        "🔎 <b>Результаты:</b>\n\n"
    )


    for number, item in enumerate(
        results,
        1
    ):


        title = html.escape(
            item["title"]
        )


        url = item["url"]


        text += (
            f"{number}. <b>{title}</b>\n"
            f"🔗 <a href=\"{url}\">Открыть</a>\n\n"
        )



    await message.edit_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=False
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
        CommandHandler(
            "creator",
            creator
        )
    )


    bot.add_handler(
        CommandHandler(
            "about",
            about
        )
    )


    bot.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search
        )
    )


    print(
        "🤖 BOT STARTED"
    )


    bot.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":

    main()
