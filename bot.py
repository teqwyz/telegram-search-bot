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


def search_startpage(query):
    url = "https://www.startpage.com/sp/search"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }

    params = {
        "query": query,
        "cat": "web",
        "language": "russian",
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=15,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for result in soup.select("div.w-gl__result"):
        link = result.select_one("a.w-gl__result-title")
        description = result.select_one("p.w-gl__description")

        if link:
            results.append({
                "title": link.get_text(" ", strip=True),
                "url": link.get("href"),
                "description": (
                    description.get_text(" ", strip=True)
                    if description
                    else ""
                ),
            })

    return results


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я бот для поиска информации в интернете.\n\n"
        "Просто отправь мне запрос, например:\n"
        "🔎 новости технологий\n"
        "🔎 кто такой Эйнштейн\n"
        "🔎 дата выхода GTA 6"
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    if not query:
        return

    message = await update.message.reply_text(
        f"🔎 Ищу:\n{query}"
    )

    try:
        results = search_startpage(query)

        if not results:
            await message.edit_text(
                "😕 По этому запросу ничего не найдено."
            )
            return

        text = "🔎 <b>Результаты поиска</b>\n\n"

        for i, result in enumerate(results[:5], 1):
            title = result["title"]
            description = result["description"]
            url = result["url"]

            text += f"<b>{i}. {title}</b>\n"

            if description:
                text += f"{description}\n"

            text += f'🔗 <a href="{url}">Открыть</a>\n\n'

        await message.edit_text(
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    except requests.Timeout:
        print("Ошибка: поисковик не ответил вовремя")

        await message.edit_text(
            "⏱ Поисковик слишком долго отвечает. "
            "Попробуй ещё раз."
        )

    except requests.RequestException as error:
        print("Ошибка подключения к поисковику:", repr(error))

        await message.edit_text(
            "❌ Не удалось подключиться к поисковику."
        )

    except Exception as error:
        print("Ошибка поиска:", repr(error))

        await message.edit_text(
            "❌ При поиске произошла ошибка."
        )


def run_web_server():
    port = int(os.environ.get("PORT", 10000))

    web_app.run(
        host="0.0.0.0",
        port=port,
    )


def main():
    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search,
        )
    )

    print("🤖 Бот запущен!")

    application.run_polling()


if __name__ == "__main__":
    main()
