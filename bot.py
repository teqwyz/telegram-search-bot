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
# МУЗЫКА
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
                url=f"vk://vk.com/audio?section=search&q={q}"
            )
        ]

    ])


# =====================
# ВИДЕО
# =====================

def video_menu(text):

    q = encode(text)

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "▶ YouTube",
                url=f"https://www.youtube.com/results?search_query={q}"
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
# WIKI / SHOP / MAPS
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
                f"https://www.wildberries.ru/catalog/0/search.aspx?search={q}"
            )

        ],

        # -----------------
        # КАРТЫ
        # -----------------

        "maps": [

            (
                "🗺 Google Maps",
                f"https://www.google.com/maps/search/{q}"
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
# WEB SEARCH
# =====================

def web_search(text):

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "Гуглить",
                url=(
                    "https://www.google.com/search"
                    f"?q={encode(text)}"
                )
            )
        ]

    ])


# =====================
# ВОПРОС О СОЗДАТЕЛЕ
# =====================

def creator_question(text):

    text = (
        text
        .lower()
        .replace("ё", "е")
    )

    phrases = [

        "кто тебя создал",
        "кто твой создатель",
        "кто тебя сделал",
        "кто тебя придумал"

    ]

    return any(
        phrase in text
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

        "Ку! Ну, я тип поисковый бот\n\n"
        "Так что выбирай что хочешь:",

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

    await query.edit_message_text(

        f"Отличный «{names.get(query.data)}» выбор.\n\n"
        "Задавай вопросы, я жду."

    )


# =====================
# СООБЩЕНИЯ
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
            "Я жду."
        )

        return


    # -----------------
    # СОЗДАТЕЛЬ
    # -----------------

    if creator_question(text):

        await update.message.reply_text(

            f"Ну смотри, меня создал {OWNER}… "
            "только никому не говори, это наш с тобой секрет"

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

            "Ну вот что я нашел:",

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

        "🌐 Веб поиск:",

        reply_markup=web_search(text)

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


    application.add_handler(

        CommandHandler(
            "start",
            start
        )

    )


    application.add_handler(

        CallbackQueryHandler(
            buttons
        )

    )


    application.add_handler(

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message
        )

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
