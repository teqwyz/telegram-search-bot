import os
import html
import threading
import requests

from flask import Flask

from bs4 import BeautifulSoup

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


BOT_TOKEN = os.environ.get("BOT_TOKEN")

PORT = int(
    os.environ.get(
        "PORT",
        10000
    )
)

OWNER = "@teqwyz"


app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram Search Bot is running!"



def run_flask():

    app.run(
        host="0.0.0.0",
        port=PORT
    )



# ======================
# ПОИСК WEB
# ======================

def web_search(text):

    try:

        r = requests.get(
            "https://www.bing.com/search",
            params={
                "q": text
            },
            headers={
                "User-Agent":
                "Mozilla/5.0"
            },
            timeout=15
        )


        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )


        result = []


        for item in soup.select(
            ".b_algo"
        ):

            title = item.select_one(
                "h2"
            )

            link = item.select_one(
                "a"
            )


            if title and link:

                result.append(
                    (
                        title.text,
                        link["href"]
                    )
                )


        return result[:5]


    except Exception as e:

        print(
            "WEB ERROR:",
            e
        )

        return []



# ======================
# ССЫЛКИ
# ======================

def q(text):

    return requests.utils.quote(
        text
    )



def music_menu(text):

    x = q(text)

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "🎵 Spotify",
                    url=f"https://open.spotify.com/search/{x}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎵 Яндекс Музыка",
                    url=f"https://music.yandex.ru/search?text={x}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎵 VK Музыка",
                    url=f"https://vk.com/search?section=audio&q={x}"
                )
            ]

        ]
    )



def video_menu(text):

    x = q(text)

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "▶ YouTube",
                    url=f"https://youtube.com/results?search_query={x}"
                )
            ]

        ]
    )



def other_menu(text, mode):

    x = q(text)


    links = {

        "news":
        [
            (
                "📰 Google Новости",
                f"https://news.google.com/search?q={x}"
            )
        ],

        "wiki":
        [
            (
                "📚 Википедия",
                f"https://ru.wikipedia.org/wiki/{x}"
            )
        ],

        "shop":
        [
            (
                "🛒 Яндекс Маркет",
                f"https://market.yandex.ru/search?text={x}"
            ),
            (
                "🛒 Ozon",
                f"https://www.ozon.ru/search/?text={x}"
            )
        ],

        "maps":
        [
            (
                "🗺 Google Maps",
                f"https://www.google.com/maps/search/{x}"
            ),
            (
                "🗺 Яндекс Карты",
                f"https://yandex.ru/maps/?text={x}"
            )
        ]

    }


    buttons = []


    for name, url in links.get(
        mode,
        []
    ):

        buttons.append(
            [
                InlineKeyboardButton(
                    name,
                    url=url
                )
            ]
        )


    return InlineKeyboardMarkup(
        buttons
    )



# ======================
# TELEGRAM
# ======================

modes = {}



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
                    "📰 Новости",
                    callback_data="news"
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
            ]

        ]
    )



async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Выбери тип поиска:",
        reply_markup=main_menu()
    )



async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    call = update.callback_query

    await call.answer()


    modes[
        call.from_user.id
    ] = call.data


    await call.edit_message_text(
        "✅ Режим выбран.\n"
        "Отправь запрос."
    )



async def message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text


    if (
        "кто тебя создал"
        in text.lower()
    ):

        await update.message.reply_text(
            f"🤖 Меня создал {OWNER}"
        )

        return



    mode = modes.get(
        update.message.from_user.id,
        "web"
    )


    if mode == "music":

        await update.message.reply_text(
            "Музыка:",
            reply_markup=music_menu(text)
        )

        return


    if mode == "video":

        await update.message.reply_text(
            "Видео:",
            reply_markup=video_menu(text)
        )

        return


    if mode in [
        "news",
        "wiki",
        "shop",
        "maps"
    ]:

        await update.message.reply_text(
            "Результат:",
            reply_markup=other_menu(
                text,
                mode
            )
        )

        return



    msg = await update.message.reply_text(
        "🔎 Ищу..."
    )


    result = web_search(
        text
    )


    if not result:

        await msg.edit_text(
            "😕 Ничего не найдено"
        )

        return



    text_answer = (
        "🌐 Результаты:\n\n"
    )


    keyboard = []


    for i, item in enumerate(
        result,
        1
    ):

        text_answer += (
            f"{i}. {html.escape(item[0])}\n"
        )


        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🔗 {i}",
                    url=item[1]
                )
            ]
        )


    await msg.edit_text(
        text_answer,
        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )
    )



# ======================
# START
# ======================

def run():

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()


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
            filters.TEXT &
            ~filters.COMMAND,
            message
        )
    )


    print(
        "BOT STARTED"
    )


    bot.run_polling()



if __name__ == "__main__":

    run()
