import os
import html
import threading
import requests

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
OWNER = "@teqwyz"

app = Flask(__name__)
modes = {}


@app.route("/")
def home():
    return "Telegram Search Bot is running!"


def run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


def encode(text: str) -> str:
    return requests.utils.quote(text, safe="")


def web_search(query: str):
    """Search DuckDuckGo Instant Answer API.
    If it has no useful results, return a direct Google search button.
    """
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
            headers={"User-Agent": "Mozilla/5.0 (Telegram Search Bot)"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        results = []

        heading = data.get("Heading")
        abstract_url = data.get("AbstractURL")
        if heading and abstract_url:
            results.append((heading, abstract_url))

        def collect(items):
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get("FirstURL") and item.get("Text"):
                    results.append((item["Text"], item["FirstURL"]))
                nested = item.get("Topics")
                if isinstance(nested, list):
                    collect(nested)

        collect(data.get("RelatedTopics", []))

        unique = []
        seen = set()
        for title, url in results:
            if url not in seen:
                seen.add(url)
                unique.append((title, url))
            if len(unique) >= 5:
                break

        if unique:
            return unique
    except Exception as exc:
        print("WEB SEARCH ERROR:", repr(exc))

    # DuckDuckGo's instant-answer endpoint may return no links for many queries.
    # Give the user a guaranteed web-search destination instead of "nothing found".
    return [("Открыть поиск Google", f"https://www.google.com/search?q={encode(query)}")]


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Веб поиск", callback_data="web")],
        [InlineKeyboardButton("🎵 Музыка", callback_data="music")],
        [InlineKeyboardButton("🎬 Видео", callback_data="video")],
    ])


def music_menu(text: str):
    query = encode(text)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🎵 Spotify",
            url=f"https://open.spotify.com/search/{query}",
        )],
        [InlineKeyboardButton(
            "🎵 Яндекс Музыка",
            url=f"https://music.yandex.ru/search?text={query}",
        )],
        [InlineKeyboardButton(
            "🎵 VK Музыка",
            # VK's general search is more reliable than the old audio URL.
            url=f"https://vk.com/search?section=audio&q={query}",
        )],
    ])


def video_menu(text: str):
    query = encode(text)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "▶️ YouTube",
            url=f"https://www.youtube.com/results?search_query={query}",
        )],
        [InlineKeyboardButton(
            "🔵 VK Видео",
            url=f"https://vk.com/video?q={query}",
        )],
        [InlineKeyboardButton(
            "🟠 Rutube",
            url=f"https://rutube.ru/search/?query={query}",
        )],
    ])


def creator_question(text: str) -> bool:
    normalized = " ".join(text.lower().replace("ё", "е").split())
    phrases = (
        "кто тебя создал",
        "кто твой создатель",
        "кто тебя сделал",
        "кто тебя придумал",
    )
    return any(phrase in normalized for phrase in phrases)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    modes[update.effective_user.id] = "web"
    await update.message.reply_text(
        "👋 Привет!\n\nВыбери тип поиска:",
        reply_markup=main_menu(),
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()
    modes[query.from_user.id] = query.data

    names = {
        "web": "🌐 Веб поиск",
        "music": "🎵 Музыка",
        "video": "🎬 Видео",
    }
    await query.edit_message_text(
        f"✅ Режим «{names.get(query.data, 'Веб поиск')}» выбран.\n\nОтправь запрос."
    )


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    original = update.message.text.strip()

    if not original:
        await update.message.reply_text("✏️ Напиши поисковый запрос.")
        return

    if creator_question(original):
        await update.message.reply_text(f"🤖 Меня создал {OWNER}")
        return

    mode = modes.get(update.effective_user.id, "web")

    if mode == "music":
        await update.message.reply_text(
            "🎵 Выбери музыкальный сервис:",
            reply_markup=music_menu(original),
        )
        return

    if mode == "video":
        await update.message.reply_text(
            "🎬 Выбери видеосервис:",
            reply_markup=video_menu(original),
        )
        return

    status = await update.message.reply_text("🔎 Ищу...")
    results = web_search(original)

    answer = "🌐 Результаты поиска:\n\n"
    keyboard = []

    for index, (title, url) in enumerate(results, 1):
        answer += f"{index}. {html.escape(title)}\n"
        keyboard.append([
            InlineKeyboardButton(f"🔗 Открыть {index}", url=url)
        ])

    await status.edit_text(
        answer,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("TELEGRAM ERROR:", repr(context.error))


def run():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set in Render Environment Variables")

    threading.Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(buttons))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message)
    )
    application.add_error_handler(error_handler)

    print("BOT STARTED")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run()
