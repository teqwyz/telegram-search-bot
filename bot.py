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
    """
    Поиск через Startpage без API-ключа.
    """

    url = "https://www.startpage.com/sp/search"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,image/webp,"
            "*/*;q=0.8"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.startpage.com/",
    }

    session = requests.Session()
    session.headers.update(headers)

    # Сначала открываем Startpage.
    # Это важно: Startpage может выдавать специальный параметр sc.
    try:
        session.get(
            "https://www.startpage.com/",
            timeout=15
        )
    except requests.RequestException:
        pass

    # Выполняем поиск
    response = session.post(
        url,
        data={
            "query": query,
            "cat": "web",
            "language": "russian",
            "lui": "russian",
        },
        timeout=20,
        allow_redirects=True,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    # Основной актуальный вариант Startpage
    result_blocks = soup.select(".w-gl__result__main")

    # Запасной вариант
    if not result_blocks:
        result_blocks = soup.select(".w-gl__result")

    for result in result_blocks:

        # Название
        title_element = result.select_one(
            ".w-gl__result-title"
        )

        if not title_element:
            title_element = result.select_one("h3")

        # Ссылка
        link_element = result.select_one(
            "a.w-gl__result-title"
        )

        if not link_element:
            link_element = result.select_one(
                "a[href]"
            )

        # Описание
        description_element = result.select_one(
            ".w-gl__description"
        )

        if not title_element or not link_element:
            continue

        title = title_element.get_text(
            " ",
            strip=True
        )

        result_url = link_element.get("href")

        description = ""

        if description_element:
            description = description_element.get_text(
                " ",
                strip=True
            )

        if not result_url:
            continue

        # Не добавляем внутренние ссылки Startpage
        if "startpage.com" in result_url:
            continue

        results.append({
            "title": title,
            "url": result_url,
            "description": description,
        })

        if len(results) >= 10:
            break

    return results


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я бот для поиска информации в интернете.\n\n"
        "Просто отправь мне запрос, например:\n"
        "🔎 новости технологий\n"
        "🔎 кто такой Эйнштейн\n"
        "🔎 дата выхода GTA 6"
    )


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
        # ВАЖНО:
        # здесь вызывается именно Startpage
        results = search_startpage(query)

        print(
            f"🔎 Запрос: {query} | "
            f"Найдено результатов: {len(results)}"
        )

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

            # Защита от проблем с HTML Telegram
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
                text += f"{description}\n"

            text += (
                f'🔗 <a href="{url}">Открыть</a>\n\n'
            )

        await message.edit_text(
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    except requests.Timeout:
        print("❌ Startpage: timeout")

        await message.edit_text(
            "⏱ Поисковик слишком долго отвечает. "
            "Попробуй ещё раз."
        )

    except requests.RequestException as error:
        print(
            "❌ Ошибка соединения с Startpage:",
            error
        )

        await message.edit_text(
            "❌ Не удалось подключиться к поисковику."
        )

    except Exception as error:
        print(
            "❌ Ошибка поиска:",
            repr(error)
        )

        await message.edit_text(
            "❌ При поиске произошла ошибка."
        )


def run_web_server():
    port = int(
        os.environ.get("PORT", 10000)
    )

    web_app.run(
        host="0.0.0.0",
        port=port,
    )


def main():

    # Flask для Render
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
        CommandHandler("start", start)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search,
        )
    )

    print("🤖 Бот запущен!")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
