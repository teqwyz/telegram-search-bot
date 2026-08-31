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
# SETTINGS
# =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

OWNER = "@teqwyz"

app = Flask(__name__)

modes = {}


# =====================
# RENDER KEEP ALIVE
# =====================

@app.route("/")
def home():
    return "🤖 Telegram Search Bot Online"


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )


# =====================
# HELPERS
# =====================

def encode(text):
    return requests.utils.quote(
        text,
        safe=""
    )


# =====================
# MENUS
# =====================

def main_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🌐 Web",
                callback_data="web"
            ),
            InlineKeyboardButton(
                "🎵 Music",
                callback_data="music"
            )
        ],

        [
            InlineKeyboardButton(
                "🎬 Video",
                callback_data="video"
            ),
            InlineKeyboardButton(
                "📚 Wiki",
                callback_data="wiki"
            )
        ],

        [
            InlineKeyboardButton(
                "🛒 Shop",
                callback_data="shop"
            ),
            InlineKeyboardButton(
                "🗺 Maps",
                callback_data="maps"
            )
        ]

    ])


# =====================
# SEARCH BUTTONS
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
                "🔎 Yandex",
                url=f"https://yandex.ru/search/?text={q}"
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
                "⬅ Menu",
                callback_data="menu"
            )
        ]

    ])


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
                "🎵 Yandex Music",
                url=f"https://music.yandex.ru/search?text={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "🎵 VK Music",
                url=f"https://vk.com/audio?section=search&q={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅ Menu",
                callback_data="menu"
            )
        ]

    ])


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
                "▶ VK Video",
                url=f"https://vk.com/video?q={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "▶ Rutube",
                url=f"https://rutube.ru/search/?query={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅ Menu",
                callback_data="menu"
            )
        ]

    ])


def other_menu(text, mode):

    q = encode(text)

    links = {

        "wiki": [
            (
                "📚 Wikipedia",
                f"https://ru.wikipedia.org/wiki/{q}"
            )
        ],

        "shop": [

            (
                "🛒 Ozon",
                f"https://www.ozon.ru/search/?text={q}"
            ),

            (
                "🛒 Wildberries",
                f"https://www.wildberries.ru/catalog/0/search.aspx?search={q}"
            ),

            (
                "🛒 Yandex Market",
                f"https://market.yandex.ru/search?text={q}"
            )

        ],

        "maps": [

            (
                "🗺 Google Maps",
                f"https://www.google.com/maps/search/?api=1&query={q}"
            ),

            (
                "🗺 Yandex Maps",
                f"https://yandex.ru/maps/?text={q}"
            ),

            (
                "🗺 2GIS",
                f"https://2gis.ru/search/{q}"
            )

        ]

    }


    buttons = []

    for name, url in links.get(mode, []):

        buttons.append(
            [
                InlineKeyboardButton(
                    name,
                    url=url
                )
            ]
        )


    buttons.append(
        [
            InlineKeyboardButton(
                "⬅ Menu",
                callback_data="menu"
            )
        ]
    )


    return InlineKeyboardMarkup(buttons)

# =====================
# START
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    modes[update.effective_user.id] = "web"

    await update.message.reply_text(

        "🤖 Привет!\n\n"
        "Я поисковый Telegram-бот.\n"
        "Выбери режим поиска:",

        reply_markup=main_menu()

    )


# =====================
# HELP
# =====================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "📌 Команды:\n\n"

        "/start — главное меню\n"
        "/help — помощь\n"
        "/about — информация\n\n"

        "Также можно использовать кнопки меню."

    )


# =====================
# ABOUT
# =====================

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "🤖 Telegram Search Bot\n\n"
        f"Создатель: {OWNER}\n\n"

        "Функции:\n"
        "🌐 Web поиск\n"
        "🎵 Музыка\n"
        "🎬 Видео\n"
        "📚 Википедия\n"
        "🛒 Магазины\n"
        "🗺 Карты"

    )


# =====================
# CALLBACK BUTTONS
# =====================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if not query:
        return


    await query.answer()


    user_id = query.from_user.id


    if query.data == "menu":

        modes[user_id] = "web"


        await query.edit_message_text(

            "🤖 Главное меню\n\n"
            "Выбери режим:",

            reply_markup=main_menu()

        )

        return


    modes[user_id] = query.data


    names = {

        "web": "🌐 Web",
        "music": "🎵 Музыка",
        "video": "🎬 Видео",
        "wiki": "📚 Wiki",
        "shop": "🛒 Покупки",
        "maps": "🗺 Карты"

    }


    await query.edit_message_text(

        "✅ Режим выбран:\n\n"
        f"{names.get(query.data)}\n\n"
        "✏️ Теперь отправь запрос",

        reply_markup=main_menu()

    )


# =====================
# MESSAGE HANDLER
# =====================

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return


    if not update.message.text:
        return


    text = update.message.text.strip()


    if not text:
        return


    user_id = update.effective_user.id


    mode = modes.get(
        user_id,
        "web"
    )


    if mode == "web":

        await update.message.reply_text(

            "🌐 Выбери поисковик:",

            reply_markup=web_search(text)

        )


    elif mode == "music":

        await update.message.reply_text(

            "🎵 Выбери сервис:",

            reply_markup=music_menu(text)

        )


    elif mode == "video":

        await update.message.reply_text(

            "🎬 Выбери сервис:",

            reply_markup=video_menu(text)

        )


    else:

        await update.message.reply_text(

            "🔎 Результаты:",

            reply_markup=other_menu(
                text,
                mode
            )

        )


# =====================
# ERROR HANDLER
# =====================

async def error_handler(update, context):

    print(
        "ERROR:",
        repr(context.error)
    )


# =====================
# RUN
# =====================

def run():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN не найден в Environment Variables"
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

        CommandHandler(
            "help",
            help_command
        )

    )


    application.add_handler(

        CommandHandler(
            "about",
            about
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


    application.add_error_handler(
        error_handler
    )


    print(
        "✅ BOT STARTED"
    )


    application.run_polling(
        drop_pending_updates=True
    )



# =====================
# MAIN
# =====================

if __name__ == "__main__":

    run()
