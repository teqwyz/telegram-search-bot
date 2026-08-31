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

PORT = int(
    os.getenv(
        "PORT",
        "10000"
    )
)

OWNER = "@teqwyz"


app = Flask(__name__)

modes = {}

history = {}



# =====================
# FLASK / RENDER
# =====================

@app.route("/")
def home():
    return "🤖 Smart Telegram Search Bot Online"



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
# УМНЫЙ АНАЛИЗ ЗАПРОСА
# =====================

def smart_detect(text):

    t = text.lower()


    music_words = [
        "песня",
        "трек",
        "музыка",
        "альбом",
        "mp3",
        "слушать"
    ]


    shop_words = [
        "купить",
        "цена",
        "заказать",
        "магазин",
        "стоимость"
    ]


    wiki_words = [
        "что такое",
        "кто такой",
        "кто такая",
        "история",
        "значение"
    ]


    maps_words = [
        "где",
        "адрес",
        "рядом",
        "карта",
        "место"
    ]


    for word in music_words:
        if word in t:
            return "music"


    for word in shop_words:
        if word in t:
            return "shop"


    for word in wiki_words:
        if word in t:
            return "wiki"


    for word in maps_words:
        if word in t:
            return "maps"


    return "web"



# =====================
# ГЛАВНОЕ МЕНЮ
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

# =====================
# КЛАВИАТУРЫ TELEGRAM
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
                "🛒 Товары",
                callback_data="shop"
            ),
            InlineKeyboardButton(
                "🗺 Карты",
                callback_data="maps"
            )
        ],

        [
            InlineKeyboardButton(
                "ℹ️ О боте",
                callback_data="about"
            )
        ]

    ])




def back_button():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "⬅ Главное меню",
                callback_data="menu"
            )
        ]

    ])





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
                "🔎 DuckDuckGo",
                url=f"https://duckduckgo.com/?q={q}"
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
                "🎵 SoundCloud",
                url=f"https://soundcloud.com/search?q={q}"
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
                "▶ Dailymotion",
                url=f"https://www.dailymotion.com/search/{q}"
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
# WIKI / SHOP / MAPS
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
                "⬅ Главное меню",
                callback_data="menu"
            )
        ]
    )


    return InlineKeyboardMarkup(buttons)





# =====================
# УМНЫЙ ПОИСК БЕЗ ИИ
# =====================

def smart_search(text):

    text_lower = text.lower()


    result = []


    keywords = {

        "музыка": "music",
        "песня": "music",
        "трек": "music",

        "фильм": "video",
        "кино": "video",
        "ютуб": "video",

        "купить": "shop",
        "цена": "shop",
        "товар": "shop",

        "где": "maps",
        "адрес": "maps",
        "карта": "maps",

        "что такое": "wiki",
        "кто такой": "wiki"

    }


    for word, mode in keywords.items():

        if word in text_lower:

            result.append(mode)



    return list(set(result))





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


    user_id = query.from_user.id



    if query.data == "menu":

        modes[user_id] = "web"


        await query.edit_message_text(

            "🤖 Главное меню\n\n"
            "Выбери способ поиска:",

            reply_markup=main_menu()

        )

        return



    modes[user_id] = query.data



    names = {

        "web":
        "🌐 Интернет",

        "music":
        "🎵 Музыка",

        "video":
        "🎬 Видео",

        "wiki":
        "📚 Знания",

        "shop":
        "🛒 Покупки",

        "maps":
        "🗺 Карты"

    }


    await query.edit_message_text(

        "✅ Режим выбран:\n\n"
        f"{names.get(query.data)}\n\n"
        "✏️ Напиши запрос",

        reply_markup=main_menu()

    )





# =====================
# START
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

        "🤖 Добро пожаловать!\n\n"

        "Я быстрый поисковый бот.\n"
        "Могу искать:\n\n"

        "🌐 сайты\n"
        "🎵 музыку\n"
        "🎬 видео\n"
        "📚 информацию\n"
        "🛒 товары\n"
        "🗺 места",

        reply_markup=main_menu()

    )





# =====================
# ОБРАБОТКА ТЕКСТА
# =====================

async def message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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



    # умный режим

    smart = smart_search(text)



    if smart and mode == "web":

        buttons = []


        for item in smart:


            if item == "music":

                buttons.append(
                    [
                        InlineKeyboardButton(
                            "🎵 Найти музыку",
                            callback_data="music"
                        )
                    ]
                )


            if item == "video":

                buttons.append(
                    [
                        InlineKeyboardButton(
                            "🎬 Найти видео",
                            callback_data="video"
                        )
                    ]
                )


            if item == "shop":

                buttons.append(
                    [
                        InlineKeyboardButton(
                            "🛒 Найти товар",
                            callback_data="shop"
                        )
                    ]
                )


            if item == "maps":

                buttons.append(
                    [
                        InlineKeyboardButton(
                            "🗺 Найти место",
                            callback_data="maps"
                        )
                    ]
                )


        buttons.append(
            [
                InlineKeyboardButton(
                    "🌐 Обычный поиск",
                    callback_data="web"
                )
            ]
        )


        await update.message.reply_text(

            "🧠 Я нашёл подходящие варианты:",

            reply_markup=InlineKeyboardMarkup(buttons)

        )


        return



    if mode == "web":

        await update.message.reply_text(

            "🌐 Поиск:",

            reply_markup=web_search(text)

        )



    elif mode == "music":

        await update.message.reply_text(

            "🎵 Музыка:",

            reply_markup=music_menu(text)

        )



    elif mode == "video":

        await update.message.reply_text(

            "🎬 Видео:",

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
# КОМАНДА HELP
# =====================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🤖 Помощь\n\n"

        "/start — открыть меню\n"
        "/help — помощь\n"
        "/about — информация\n\n"

        "Доступные режимы:\n"

        "🌐 Интернет\n"
        "🎵 Музыка\n"
        "🎬 Видео\n"
        "📚 Википедия\n"
        "🛒 Товары\n"
        "🗺 Карты\n\n"

        "Также работает автоматический умный поиск."

    )





# =====================
# ABOUT
# =====================

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🤖 Telegram Search Bot\n\n"

        f"Создатель: {OWNER}\n\n"

        "Возможности:\n"

        "✅ быстрый поиск\n"
        "✅ умные категории без ИИ\n"
        "✅ музыка\n"
        "✅ видео\n"
        "✅ товары\n"
        "✅ карты\n\n"

        "Версия: 2.0"

    )





# =====================
# КОМАНДЫ РЕЖИМОВ
# =====================

async def set_mode(
    update: Update,
    mode,
    text
):

    modes[
        update.effective_user.id
    ] = mode


    await update.message.reply_text(

        f"{text}\n\n"
        "✏️ Отправь запрос."

    )





async def music_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await set_mode(
        update,
        "music",
        "🎵 Режим музыки включён"
    )





async def video_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await set_mode(
        update,
        "video",
        "🎬 Режим видео включён"
    )





async def wiki_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await set_mode(
        update,
        "wiki",
        "📚 Режим Википедии включён"
    )





async def shop_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await set_mode(
        update,
        "shop",
        "🛒 Режим товаров включён"
    )





async def maps_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await set_mode(
        update,
        "maps",
        "🗺 Режим карт включён"
    )





# =====================
# ERROR
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
            "BOT_TOKEN отсутствует в Environment Variables"
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



    # команды

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



    # кнопки

    application.add_handler(

        CallbackQueryHandler(
            buttons
        )

    )



    # сообщения

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
