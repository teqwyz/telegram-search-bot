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
    filters
)


BOT_TOKEN = os.environ["BOT_TOKEN"]


# Веб-сервер для Render
web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Telegram Search Bot is running!"


# Поиск через DuckDuckGo
def search_duckduckgo(query):

    url = "https://html.duckduckgo.com/html/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/150.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9"
    }

    response = requests.get(
        url,
        params={"q": query},
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

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

        title = link.get_text(
            " ",
            strip=True
        )

        result_url = link.get(
            "href"
        )

        description_block = item.select_one(
            ".result__snippet"
        )

        description = ""

        if description_block:
            description = description_block.get_text(
                " ",
                strip=True
            )

        results.append({
            "title": title,
            "url": result_url,
            "description": description
        })

    return results



# Команда /start
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я бот для поиска информации в интернете.\n\n"
        "Отправь запрос, например:\n\n"
        "🔎 новости технологий\n"
        "🔎 кто такой Эйнштейн\n"
        "🔎 дата выхода GTA 6"
    )



# Обработка сообщений
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


        print(
            "Запрос:",
            query
        )

        print(
            "Найдено:",
            len(results)
        )


        if not results:

            await message.edit_text(
                "😕 По этому запросу ничего не найдено."
            )

            return



        text = (
            "🔎 <b>Результаты поиска</b>\n\n"
        )


        for i, result in enumerate(
            results[:5],
            1
        ):

            text += (
                f"<b>{i}. "
                f"{result['title']}</b>\n"
            )


            if result["description"]:

                text += (
                    result["description"]
                    + "\n"
                )


            text += (
                f"🔗 "
                f"<a href=\"{result['url']}\">"
                "Открыть"
                "</a>\n\n"
            )


        await message.edit_text(
            text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )


    except Exception as error:

        print(
            "Ошибка поиска:",
            repr(error)
        )


        await message.edit_text(
            "❌ Ошибка при поиске."
        )



# Запуск Flask для Render
def run_web_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    web_app.run(
        host="0.0.0.0",
        port=port
    )



# Запуск бота
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


    application.run_polling()



if __name__ == "__main__":

    main()


if __name__ == "__main__":
    main()
