import os
import html
import threading
import requests

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)


# =====================
# НАСТРОЙКИ
# =====================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

PORT = int(
    os.environ.get(
        "PORT",
        10000
    )
)

OWNER = "@teqwyz"


# =====================
# FLASK
# =====================

app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram Search Bot is running!"


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT
    )


# =====================
# РЕЖИМЫ
# =====================

modes = {}


# =====================
# КОДИРОВАНИЕ URL
# =====================

def encode(text):
    return requests.utils.quote(
        text,
        safe=""
    )


# =====================
# ВЕБ-ПОИСК
# =====================

def web_search(query):

    results = []

    try:

        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            },
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        # Основной результат

        if (
            data.get("Heading")
            and data.get("AbstractURL")
        ):

            results.append(
                (
                    data["Heading"],
                    data["AbstractURL"]
                )
            )

        # Связанные результаты

        for item in data.get(
            "RelatedTopics",
            []
        ):

            if not isinstance(
                item,
                dict
            ):
                continue

            title = item.get(
                "Text"
            )

            url = item.get(
                "FirstURL"
            )

            if title and url:

                results.append(
                    (
                        title,
                        url
                    )
                )

        if results:

            return results[:5]

    except Exception as e:

        print(
            "WEB SEARCH ERROR:",
            repr(e)
        )

    # Запасной вариант

    return [
        (
            "🔎 Открыть поиск Google",
            "https://www.google.com/search?q="
            + encode(query)
        )
    ]


# =====================
# ГЛАВНОЕ МЕНЮ
# =====================

def main_menu():

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "🌐 Веб",
                    callback_data="web"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎵 Музыка",
                    callback_data="music"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎬 Видео",
                    callback_data="video"
                )
            ],

            [
                InlineKeyboardButton(
                    "📰 Новости",
                    callback_data="news"
                )
            ],

            [
                InlineKeyboardButton(
                    "📚 Википедия",
                    callback_data="wiki"
                )
            ]

        ]
    )


# =====================
# МУЗЫКА
# =====================

def music_menu(text):

    query = encode(text)

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "🎵 Spotify",
                    url=(
                        "https://open.spotify.com/search/"
                        + query
                    )
                )
            ],

            [
                InlineKeyboardButton(
                    "🎵 Яндекс Музыка",
                    url=(
                        "https://music.yandex.ru/search?text="
                        + query
                    )
                ],

            [
                InlineKeyboardButton(
                    "🎵 VK Музыка",
                    url=(
                        "https://vk.com/search?"
                        "c%5Bsection%5D=audio&"
                        "c%5Bq%5D="
                        + query
                    )
                )
            ]

        ]
    )


# =====================
# ВИДЕО
# =====================

def video_menu(text):

    query = encode(text)

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "📺 YouTube",
                    url=(
                        "https://www.youtube.com/results?"
                        "search_query="
                        + query
                    )
                )
            ],

            [
                InlineKeyboardButton(
                    "📺 VK Видео",
                    url=(
                        "https://vkvideo.ru/"
                        "?q="
                        + query
                    )
                )
            ],

            [
                InlineKeyboardButton(
                    "📺 Rutube",
                    url=(
                        "https://rutube.ru/search/"
                        "?query="
                        + query
                    )
                )
            ]

        ]
    )


# =====================
# СТАРТ
# =====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    await update.message.reply_text(
        "Ку!\n\n"
        "Ну вообщем, я типа поисковый бот.\n"
        "Так что, выбирай тип поиска:",
        reply_markup=main_menu()
    )


# =====================
# КНОПКИ
# =====================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    modes[
        query.from_user.id
    ] = query.data

    names = {
        "web": "🌐 Веб-поиск",
        "music": "🎵 Музыка",
        "video": "🎬 Видео",
        "news": "📰 Новости",
        "wiki": "📚 Википедия"
    }

    mode_name = names.get(
        query.data,
        "Поиск"
    )

    await query.edit_message_text(
        f"✅ Хороший выбор!: {mode_name}\n\n"
        "Теперь отправь свой запрос."
    )


# =====================
# СОЗДАТЕЛЬ
# =====================

def is_creator_question(text):

    text = (
        text
        .lower()
        .strip()
        .replace("ё", "е")
    )

    questions = [

        "кто тебя создал",
        "кто тебя сделал",
        "кто твой создатель",
        "кто создатель",
        "кто автор",
        "кто тебя написал",
        "кто разработал тебя",
        "кто тебя разработал",
        "кто тебя придумал",

        "кто тебя создал?",
        "кто тебя сделал?",
        "кто твой создатель?",
        "кто создатель?",
        "кто автор?",
        "кто тебя написал?",
        "кто разработал тебя?",
        "кто тебя разработал?",
        "кто тебя придумал?"

    ]

    return text in questions


# =====================
# СООБЩЕНИЯ
# =====================

async def message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text.strip()

    # =====================
    # СОЗДАТЕЛЬ
    # =====================

    if is_creator_question(text):

        await update.message.reply_text(
            "🤖 Меня создал @teqwyz"
        )

        return

    # =====================
    # РЕЖИМ
    # =====================

    user_id = update.message.from_user.id

    mode = modes.get(
        user_id,
        "web"
    )

    # =====================
    # МУЗЫКА
    # =====================

    if mode == "music":

        await update.message.reply_text(
            "🎵 Музыка:",
            reply_markup=music_menu(
                text
            )
        )

        return

    # =====================
    # ВИДЕО
    # =====================

    if mode == "video":

        await update.message.reply_text(
            "🎬 Видео:",
            reply_markup=video_menu(
                text
            )
        )

        return

    # =====================
    # НОВОСТИ
    # =====================

    if mode == "news":

        query = encode(text)

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📰 Google Новости",
                        url=(
                            "https://news.google.com/search?q="
                            + query
                        )
                    )
                ]
            ]
        )

        await update.message.reply_text(
            "📰 Новости:",
            reply_markup=keyboard
        )

        return

    # =====================
    # ВИКИПЕДИЯ
    # =====================

    if mode == "wiki":

        query = encode(text)

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📚 Википедия",
                        url=(
                            "https://ru.wikipedia.org/wiki/"
                            + query
                        )
                    )
                ]
            ]
        )

        await update.message.reply_text(
            "📚 Википедия:",
            reply_markup=keyboard
        )

        return

    # =====================
    # ВЕБ-ПОИСК
    # =====================

    msg = await update.message.reply_text(
        "🔎 Ищу..."
    )

    results = web_search(
        text
    )

    if not results:

        await msg.edit_text(
            "😕 Ничего не найдено.\n\n"
            "Попробуй изменить запрос."
        )

        return

    answer = (
        "🌐 <b>Результаты поиска:</b>\n\n"
    )

    keyboard = []

    for i, item in enumerate(
        results,
        1
    ):

        title = item[0]
        url = item[1]

        answer += (
            f"{i}. "
            f"{html.escape(title[:150])}\n\n"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🔗 Открыть {i}",
                    url=url
                )
            ]
        )

    await msg.edit_text(
        answer,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =====================
# ОШИБКИ
# =====================

async def error_handler(
    update,
    context
):

    print(
        "BOT ERROR:",
        repr(context.error)
    )


# =====================
# ЗАПУСК
# =====================

def run():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN не найден! "
            "Добавь BOT_TOKEN в Environment Variables Render."
        )

    # Flask для Render

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    # Telegram

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
        CallbackQueryHandler(
            buttons
        )
    )

    bot.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            message
        )
    )

    bot.add_error_handler(
        error_handler
    )

    print(
        "BOT STARTED"
    )

    bot.run_polling(
        drop_pending_updates=True
    )


# =====================
# MAIN
# =====================

if __name__ == "__main__":
    run()
