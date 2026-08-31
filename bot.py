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



# =====================
# FLASK / RENDER
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
# URL
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
                url=f"https://vk.com/audio?section=search&q={q}"
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
        ]

    ])

# =====================
# ВИКИ / ТОВАРЫ / КАРТЫ
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
            ),

            (
                "🗺 Apple Maps",
                f"https://maps.apple.com/?q={q}"
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
                "🔎 Яндекс",
                url=f"https://yandex.ru/search/?text={q}"
            )

        ],


        [

            InlineKeyboardButton(
                "🔎 Bing",
                url=f"https://www.bing.com/search?q={q}"
            )

        ]

    ])




# =====================
# СОЗДАТЕЛЬ
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
        p in text
        for p in phrases
    )




# =====================
# КНОПКИ МЕНЮ
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


    modes[user_id] = query.data



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

        f"{name}\n\n"
        "✅ Режим выбран.\n"
        "Отправь запрос.",

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


    user_id = update.effective_user.id


    modes[user_id] = "web"


    await update.message.reply_text(

        "🤖 Привет!\n\n"
        "Я поисковый Telegram-бот.\n"
        "Выбери нужный режим:",

        reply_markup=main_menu()

    )




# =====================
# HELP
# =====================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "📌 Команды:\n\n"

        "/start — меню\n"
        "/help — помощь\n"
        "/about — информация\n"
        "/music — музыка\n"
        "/video — видео\n"
        "/wiki — Википедия\n"
        "/shop — товары\n"
        "/maps — карты"

    )




# =====================
# ABOUT
# =====================

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🤖 Поисковый бот\n\n"
        f"Создатель: {OWNER}\n\n"
        "Функции:\n"
        "🌐 поиск\n"
        "🎵 музыка\n"
        "🎬 видео\n"
        "📚 Википедия\n"
        "🛒 товары\n"
        "🗺 карты"

    )




# =====================
# УСТАНОВКА РЕЖИМА
# =====================

async def set_mode(
    update: Update,
    mode,
    title
):

    modes[
        update.effective_user.id
    ] = mode


    await update.message.reply_text(

        f"{title}\n\n"
        "Теперь отправь запрос."

    )




# =====================
# КОМАНДЫ
# =====================

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



    # Проверка создателя

    if creator_question(text):

        await update.message.reply_text(

            f"🤖 Меня создал {OWNER}"

        )

        return



    user_id = update.effective_user.id



    mode = modes.get(
        user_id,
        "web"
    )



    if mode == "music":

        await update.message.reply_text(

            "🎵 Выбери сервис:",

            reply_markup=music_menu(text)

        )

        return




    if mode == "video":

        await update.message.reply_text(

            "🎬 Выбери сервис:",

            reply_markup=video_menu(text)

        )

        return




    if mode in [

        "wiki",
        "shop",
        "maps"

    ]:

        await update.message.reply_text(

            "🔎 Результаты:",

            reply_markup=other_menu(
                text,
                mode
            )

        )

        return




    await update.message.reply_text(

        "🌐 Поиск:",

        reply_markup=web_search(text)

    )

# =====================
# ERROR HANDLER
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
            "BOT_TOKEN не найден в Environment Variables"
        )



    # Запуск Flask для Render

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



    # =====================
    # КОМАНДЫ
    # =====================


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



    # =====================
    # КНОПКИ
    # =====================

    application.add_handler(

        CallbackQueryHandler(
            buttons
        )

    )



    # =====================
    # ТЕКСТ
    # =====================

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
