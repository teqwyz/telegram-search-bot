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
                url=f"https://vk.ru/audios866956338"
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
        ]

    ])





# =====================
# ДРУГИЕ СЕРВИСЫ
# =====================

def other_menu(text, mode):

    q = encode(text)


    links = {


        "wiki":[

            (
                "📚 Википедия",
                f"https://ru.wikipedia.org/wiki/{q}"
            )

        ],


        "shop":[

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

        "maps":[

            (
                "🗺 Google Maps",
                f"https://www.google.com/maps/search/{q}"
            ),

            (
                "🗺 Яндекс Карты",
                f"https://yandex.ru/maps/?text={q}"
            )

        ]

    }


    buttons=[]


    for name,url in links.get(mode,[]):

        buttons.append([

            InlineKeyboardButton(
                name,
                url=url
            )

        ])


    return InlineKeyboardMarkup(buttons)





# =====================
# WEB ПОИСК
# =====================

def web_search(text):

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(

                "🔎 Открыть Google",

                url=f"https://www.google.com/search?q={encode(text)}"

            )

        ]

    ])





# =====================
# СОЗДАТЕЛЬ
# =====================

def creator_question(text):

    t = text.lower().replace(
        "ё",
        "е"
    )


    return any(

        x in t

        for x in [

            "кто тебя создал",

            "кто твой создатель",

            "кто тебя сделал",

            "кто тебя придумал"

        ]

    )





# =====================
# TELEGRAM
# =====================

async def start(
    update:Update,
    context:ContextTypes.DEFAULT_TYPE
):

    modes[
        update.effective_user.id
    ] = "web"


    await update.message.reply_text(

        "Ку! Ну чо, я тип поисковый бот...\n\nВыбирай что хочешь:",

        reply_markup=main_menu()

    )





async def buttons(
    update:Update,
    context:ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    await query.answer()


    modes[
        query.from_user.id
    ] = query.data


    await query.edit_message_text(

        "Хорошый выбор.\nОтправляй запрос."

    )





async def message(
    update:Update,
    context:ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()



    if creator_question(text):

        await update.message.reply_text(

            f"Ну смотри, меня создал {OWNER}... только не говори, что это я тебе сказал."

        )

        return



    mode = modes.get(

        update.effective_user.id,

        "web"

    )



    if mode=="music":

        await update.message.reply_text(

            "🎵 Музыка:",

            reply_markup=music_menu(text)

        )

        return



    if mode=="video":

        await update.message.reply_text(

            "🎬 Видео:",

            reply_markup=video_menu(text)

        )

        return



    if mode in [

        "wiki",

        "shop",

        "maps"

    ]:


        await update.message.reply_text(

            "🔎 Поиск:",

            reply_markup=other_menu(
                text,
                mode
            )

        )

        return



    await update.message.reply_text(

        "🌐 Веб поиск:",

        reply_markup=web_search(text)

    )





# =====================
# START BOT
# =====================

def run():


    threading.Thread(

        target=run_flask,

        daemon=True

    ).start()



    application=(

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



    print(
        "BOT STARTED"
    )


    application.run_polling()





if __name__=="__main__":

    run()
