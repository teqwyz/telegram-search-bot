import os
import threading
import requests

from bs4 import BeautifulSoup
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Telegram Search Bot is running!"

def search_duckduckgo(query):
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/150.0 Safari/537.36"
        )
    }

    response = requests.post(
        url,
        data={"q": query},
        headers=headers,
        timeout=15
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for result in soup.select(".result"):
        title = result.select_one(".result__title")
        link = result.select_one(".result__a")
        description = result.select_one(".result__snippet")

        if title and link:
            results.append({
                "title": title.get_text(" ", strip=True),
                "url": link.get("href"),
                "description": (
                    description.get_text(" ", strip=True)
                    if description else ""
                )
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

    message = await update.message.reply_text(f"🔎 Ищу:\n{query}")

    try:
        results = search_duckduckgo(query)

        if not results:
            await message.edit_text("😕 По этому запросу ничего не найдено.")
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
            disable_web_page_preview=True
        )

    except Exception as error:
        print("Ошибка поиска:", error)
        await message.edit_text("❌ При поиске произошла ошибка.")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

def main():
    threading.Thread(target=run_web_server, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search)
    )

    print("🤖 Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
