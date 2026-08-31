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
# FLASK RENDER
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
# URL
# =====================

def encode(text):

    return requests.utils.quote(
        text,
        safe=""
    )



# =====================
# КРАСИВОЕ ГЛАВНОЕ МЕНЮ
# =====================

def main_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🌐 Интернет",
                callback_data="web"
            ),

            InlineKeyboardButton(
                "🎵 Музыка",
                callback_data="music"
            )
        ],

        [
            InlineKeyboardButton(
                "🎬 Видео",
                callback_data="video"
            ),

            InlineKeyboardButton(
                "📚 Знания",
                callback_data="wiki"
            )
        ],

        [
            InlineKeyboardButton(
                "🛒 Покупки",
                callback_data="shop"
            ),

            InlineKeyboardButton(
                "🗺 Карты",
                callback_data="maps"
            )
        ]

    ])



def back_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "⬅ Главное меню",
                callback_data="menu"
            )
        ]

    ])



# =====================
# ПОИСК В ИНТЕРНЕТЕ
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
                "🔎 Яндекс",
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
                "⬅ Меню",
                callback_data="menu"
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
                url=f"https://vk.com/audio?section=search&q={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅ Меню",
                callback_data="menu"
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
                url=f"https://youtube.com/results?search_query={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "▶ VK Видео",
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
                "⬅ Меню",
                callback_data="menu"
            )
        ]

    ])

# =====================
# КРАСИВОЕ ГЛАВНОЕ МЕНЮ
# =====================

def main_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🌐 Веб",
                callback_data="web"
            ),
            InlineKeyboardButton(
                "🎵 Музыка",
                callback_data="music"
            )
        ],

        [
            InlineKeyboardButton(
                "🎬 Видео",
                callback_data="video"
            ),
            InlineKeyboardButton(
                "📚 Wiki",
                callback_data="wiki"
            )
        ],

        [
            InlineKeyboardButton(
                "🛒 Товары",
                callback_data="shop"
            ),
            InlineKeyboardButton(
                "🗺 Карты",
                callback_data="maps"
            )
        ]

    ])





# =====================
# КНОПКА НАЗАД
# =====================

def back_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "⬅️ Главное меню",
                callback_data="back"
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
                url=f"https://vk.com/audio?section=search&q={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="back"
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
                "⬅️ Назад",
                callback_data="back"
            )
        ]

    ])

# =====================
# WIKI / ТОВАРЫ / КАРТЫ
# =====================

def other_menu(text, mode):

    q = encode(text)

    links = {

        "wiki": [
            (
                "📚 Википедия",
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
                "🛒 Яндекс Маркет",
                f"https://market.yandex.ru/search?text={q}"
            )
        ],


        "maps": [

            (
                "🗺 Google Maps",
                f"https://www.google.com/maps/search/?api=1&query={q}"
            ),

            (
                "🗺 Яндекс Карты",
                f"https://yandex.ru/maps/?text={q}"
            ),

            (
                "🗺 2ГИС",
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
                "⬅️ Главное меню",
                callback_data="menu"
            )
        ]
    )


    return InlineKeyboardMarkup(buttons)




# =====================
# КНОПКИ
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
            "Выбери режим поиска:",

            reply_markup=main_menu()

        )

        return



    modes[user_id] = query.data


    names = {

        "web": "🌐 Веб поиск",
        "music": "🎵 Музыка",
        "video": "🎬 Видео",
        "wiki": "📚 Википедия",
        "shop": "🛒 Товары",
        "maps": "🗺 Карты"

    }


    await query.edit_message_text(

        "✅ Выбран режим:\n\n"
        f"{names.get(query.data)}\n\n"
        "✏️ Теперь отправь запрос",

        reply_markup=main_menu()

    )




# =====================
# ОБРАБОТКА СООБЩЕНИЙ
# =====================

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return


    text = update.message.text


    if not text:
        return


    user_id = update.effective_user.id


    mode = modes.get(
        user_id,
        "web"
    )


    if mode == "web":

        await update.message.reply_text(
            "🌐 Поисковики:",
            reply_markup=web_search(text)
        )


    elif mode in [
        "music",
        "video"
    ]:

        if mode == "music":

            await update.message.reply_text(
                "🎵 Где искать музыку:",
                reply_markup=music_menu(text)
            )

        else:

            await update.message.reply_text(
                "🎬 Где искать видео:",
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
# ERROR
# =====================

async def error_handler(update, context):

    print(
        "ERROR:",
        context.error
    )




# =====================
# ЗАПУСК
# =====================

def run():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN не найден"
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


    application.add_error_handler(
        error_handler
    )


    print(
        "✅ BOT STARTED"
    )


    application.run_polling()



if __name__ == "__main__":

    run()
