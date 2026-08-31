import os
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

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
OWNER = "@teqwyz"

app = Flask(__name__)
modes = {}


# =====================
# RENDER / FLASK
# =====================

@app.route("/")
def home():
    return "Telegram Search Bot is running!"


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )


# =====================
# URL ENCODING
# =====================

def encode(text):
    return requests.utils.quote(
        text,
        safe=""
    )


# =====================
# ГЛАВНОЕ МЕНЮ
# =====================

def main_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🌐 Веб поиск",
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
                "📚 Википедия",
                callback_data="wiki"
            )
        ],

        [
            InlineKeyboardButton(
                "🛒 Товары",
                callback_data="shop"
            )
        ],

        [
            InlineKeyboardButton(
                "🗺 Карты",
                callback_data="maps"
            )
        ]

    ])


# =====================
# МЕНЮ МУЗЫКИ
# =====================

def music_menu(text):

    q = encode(text)

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🎵 Spotify",
                url=f"https://open.spotify.com/search/{q}"
            )
        ],

        [
            InlineKeyboardButton(
                "🎵 Яндекс Музыка",
                url=f"https://music.yandex.ru/search?text={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "🎵 VK Музыка",
                url=f"https://vk.com/audio?section=search&q={q}"
            )
        ]

    ])


# =====================
# МЕНЮ ВИДЕО
# =====================

def video_menu(text):

    q = encode(text)

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "▶ YouTube",
                url=(
                    "https://www.youtube.com/results"
                    f"?search_query={q}"
                )
            )
        ],

        [
            InlineKeyboardButton(
                "▶ VK Видео",
                url=f"https://vk.com/video/search?q={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "▶ Rutube",
                url=f"https://rutube.ru/search/?query={q}"
            )
        ]

    ])


# =====================
# ВИКИ / ТОВАРЫ / КАРТЫ
# =====================

def other_menu(text, mode):

    q = encode(text)

    links = {

        # -----------------
        # ВИКИПЕДИЯ
        # -----------------

        "wiki": [

            (
                "📚 Википедия",
                f"https://ru.wikipedia.org/wiki/{q}"
            )

        ],

        # -----------------
        # ТОВАРЫ
        # -----------------

        "shop": [

            (
                "🛒 Яндекс Маркет",
                f"https://market.yandex.ru/search?text={q}"
            ),

            (
                "🛒 Ozon",
                f"https://www.ozon.ru/search/?text={q}"
            ),

            (
                "🛒 Wildberries",
                (
                    "https://www.wildberries.ru/catalog/0/"
                    f"search.aspx?search={q}"
                )
            )

        ],

        # -----------------
        # КАРТЫ
        # -----------------

        "maps": [

            (
                "🗺 Google Maps",
                (
                    "https://www.google.com/maps/search/"
                    f"?api=1&query={q}"
                )
            ),

            (
                "🗺 Яндекс Карты",
                f"https://yandex.ru/maps/?text={q}"
            ),

            (
                "🗺 2ГИС",
                f"https://2gis.ru/search/{q}"
            ),

            (
                "🗺 Apple Maps",
                f"https://maps.apple.com/?q={q}"
            )

        ]

    }

    buttons = []

    for name, url in links.get(mode, []):

        buttons.append([

            InlineKeyboardButton(
                name,
                url=url
            )

        ])

    return InlineKeyboardMarkup(buttons)


# =====================
# ВЕБ ПОИСК
# =====================

def web_search(text):

    q = encode(text)

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🔎 Google",
                url=f"https://www.google.com/search?q={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "🔎 Bing",
                url=f"https://www.bing.com/search?q={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "🔎 DuckDuckGo",
                url=f"https://duckduckgo.com/?q={q}"
            )
        ]

    ])


# =====================
# ПРОВЕРКА СОЗДАТЕЛЯ
# =====================

def creator_question(text):

    normalized = (
        text
        .lower()
        .replace("ё", "е")
    )

    phrases = (

        "кто тебя создал",
        "кто твой создатель",
        "кто тебя сделал",
        "кто тебя придумал",
        "кто создал тебя",
        "кто сделал тебя"

    )

    return any(
        phrase in normalized
        for phrase in phrases
    )


# =====================
# /START
# =====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    modes[
        update.effective_user.id
    ] = "web"

    await update.message.reply_text(

        "Ку! Ну я тип поисковый бот.\n\n"
        "Так что, выбирай, что хочешь:",

        reply_markup=main_menu()

    )


# =====================
# /HELP
# =====================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🤖 Помощь\n\n"

        "/start — главное меню\n"
        "/help — список команд\n"
        "/about — информация о боте\n\n"

        "🔎 Режимы поиска:\n"
        "/music — музыка\n"
        "/video — видео\n"
        "/wiki — Википедия\n"
        "/shop — товары\n"
        "/maps — карты\n\n"

        "Также можно использовать кнопки "
        "главного меню."

    )


# =====================
# /ABOUT
# =====================

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "Я поисковый Telegram-бот\n\n"
        f"Меня создал: {OWNER}\n"
        "Поддерживаются поиск, музыка, видео, "
        "Википедия, товары и карты."

    )


# =====================
# УСТАНОВКА РЕЖИМА
# =====================

async def set_mode(
    update: Update,
    mode,
    title
):

    if not update.message:
        return

    modes[
        update.effective_user.id
    ] = mode

    await update.message.reply_text(

        f"{title}? Без проблем.\n\n"
        "Что хочешь найти?"

    )


# =====================
# КОМАНДЫ ПОИСКА
# =====================

async def music_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await set_mode(
        update,
        "music",
        "🎵 Музыка"
    )


async def video_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await set_mode(
        update,
        "video",
        "🎬 Видео"
    )


async def wiki_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await set_mode(
        update,
        "wiki",
        "📚 Википедия"
    )


async def shop_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await set_mode(
        update,
        "shop",
        "🛒 Товары"
    )


async def maps_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await set_mode(
        update,
        "maps",
        "🗺 Карты"
    )


# =====================
# КНОПКИ
# =====================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    modes[
        query.from_user.id
    ] = query.data

    names = {

        "web":
            "🌐 Веб поиск",

        "music":
            "🎵 Музыка",

        "video":
            "🎬 Видео",

        "wiki":
            "📚 Википедия",

        "shop":
            "🛒 Товары",

        "maps":
            "🗺 Карты"

    }

    name = names.get(
        query.data,
        "🌐 Веб поиск"
    )

    await query.edit_message_text(

        f"{name}? Без прооблем.\n\n"
        "Что хочешь найти?"

    )


# =====================
# ОБРАБОТКА СООБЩЕНИЙ
# =====================

async def message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    if not text:

        await update.message.reply_text(
            "✏️ Напиши поисковый запрос."
        )

        return


    # -----------------
    # СОЗДАТЕЛЬ
    # -----------------

    if creator_question(text):

        await update.message.reply_text(

            f"Ну смотри, меня создал {OWNER}... только не кому не рассказывай, это наш с тобой секрет."

        )

        return


    mode = modes.get(

        update.effective_user.id,

        "web"

    )


    # -----------------
    # МУЗЫКА
    # -----------------

    if mode == "music":

        await update.message.reply_text(

            "🎵 Выбирай, где будешь слушать музыку:",

            reply_markup=music_menu(text)

        )

        return


    # -----------------
    # ВИДЕО
    # -----------------

    if mode == "video":

        await update.message.reply_text(

            "🎬 Выбирай, где будешь смотреть видосы:",

            reply_markup=video_menu(text)

        )

        return


    # -----------------
    # WIKI / SHOP / MAPS
    # -----------------

    if mode in [

        "wiki",
        "shop",
        "maps"

    ]:

        await update.message.reply_text(

            "🔎 Ну смотри, вот что я нашел:",

            reply_markup=other_menu(
                text,
                mode
            )

        )

        return


    # -----------------
    # WEB
    # -----------------

    await update.message.reply_text(

        "🌐 Выбирай поисковик:",

        reply_markup=web_search(text)

    )


# =====================
# ОШИБКИ
# =====================

async def error_handler(
    update,
    context
):

    print(
        "TELEGRAM ERROR:",
        repr(context.error)
    )


# =====================
# ЗАПУСК
# =====================

def run():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN не найден в Environment Variables Render"
        )


    threading.Thread(

        target=run_flask,
        daemon=True

    ).start()


    application = (

        Application
        .builder()
        .token(BOT_TOKEN)
        .build()

    )


    # -----------------
    # КОМАНДЫ
    # -----------------

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CommandHandler(
            "about",
            about_command
        )
    )

    application.add_handler(
        CommandHandler(
            "music",
            music_command
        )
    )

    application.add_handler(
        CommandHandler(
            "video",
            video_command
        )
    )

    application.add_handler(
        CommandHandler(
            "wiki",
            wiki_command
        )
    )

    application.add_handler(
        CommandHandler(
            "shop",
            shop_command
        )
    )

    application.add_handler(
        CommandHandler(
            "maps",
            maps_command
        )
    )


    # -----------------
    # КНОПКИ
    # -----------------

    application.add_handler(

        CallbackQueryHandler(
            buttons
        )

    )


    # -----------------
    # ТЕКСТ
    # -----------------

    application.add_handler(

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message
        )

    )


    application.add_error_handler(
        error_handler
    )


    print("BOT STARTED")


    application.run_polling(
        drop_pending_updates=True
    )


# =====================
# MAIN
# =====================

if __name__ == "__main__":

    run()
