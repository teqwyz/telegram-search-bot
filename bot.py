import os
import asyncio
import threading
from urllib.parse import quote

from flask import Flask, request

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


# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.environ["BOT_TOKEN"]

PORT = int(
    os.environ.get(
        "PORT",
        10000
    )
)

RENDER_URL = (
    "https://telegram-search-bot-g9vr.onrender.com"
)


# =========================
# GLOBAL
# =========================

app = Flask(__name__)

telegram_app = None

telegram_loop = None

user_queries = {}



# =========================
# FLASK
# =========================


@app.route("/")
def home():

    return "Telegram Search Bot is running!"



@app.route(
    f"/{BOT_TOKEN}",
    methods=["POST"]
)
def webhook():

    try:

        data = request.get_json()

        update = Update.de_json(
            data,
            telegram_app.bot
        )


        asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update),
            telegram_loop
        )


    except Exception as e:

        print(
            "Webhook error:",
            e
        )


    return "OK"



# =========================
# START
# =========================


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я поисковый бот 🔎\n\n"
        "Ищу:\n"
        "🌐 сайты\n"
        "🎵 музыку\n"
        "🎬 видео\n\n"
        "Просто напиши запрос."
    )



async def creator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🤖 Меня создал @teqwyz"
    )



# =========================
# MESSAGE
# =========================


async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    user_id = update.message.from_user.id


    if (
        "кто тебя создал"
        in text.lower()
        or
        "кто твой создатель"
        in text.lower()
    ):

        await creator(
            update,
            context
        )

        return



    user_queries[user_id] = text


    keyboard = [

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
                "🌐 Сайты",
                callback_data="sites"
            )
        ]

    ]


    await update.message.reply_text(
        f"🔎 Поиск: <b>{text}</b>\n\n"
        "Выбери категорию:",
        parse_mode="HTML",
        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )
    )



# =========================
# BUTTONS
# =========================


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    user_id = query.from_user.id


    text = user_queries.get(
        user_id,
        ""
    )


    if not text:

        await query.edit_message_text(
            "❌ Запрос потерян. Напиши его заново."
        )

        return



    encoded = quote(text)



    # MUSIC

    if query.data == "music":


        keyboard = [

            [
                InlineKeyboardButton(
                    "🎵 Яндекс Музыка",
                    url=
                    (
                        "https://music.yandex.ru/search?"
                        f"text={encoded}"
                    )
                )
            ],


            [
                InlineKeyboardButton(
                    "🎵 VK Музыка",
                    url=
                    (
                        "https://vk.com/audios?"
                        f"q={encoded}"
                    )
                )
            ]

        ]


        await query.edit_message_text(
            f"🎵 Музыка:\n\n{text}",
            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )
        )



    # VIDEO

    elif query.data == "video":


        keyboard = [

            [
                InlineKeyboardButton(
                    "🎬 YouTube",
                    url=
                    (
                        "https://youtube.com/results?"
                        f"search_query={encoded}"
                    )
                )
            ]

        ]


        await query.edit_message_text(
            f"🎬 Видео:\n\n{text}",
            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )
        )



    # SITES

    elif query.data == "sites":


        keyboard = [

            [
                InlineKeyboardButton(
                    "🌐 Google",
                    url=
                    (
                        "https://www.google.com/search?"
                        f"q={encoded}"
                    )
                )
            ]

        ]


        await query.edit_message_text(
            f"🌐 Сайты:\n\n{text}",
            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )
        )



# =========================
# TELEGRAM
# =========================


async def setup_bot():

    global telegram_app


    telegram_app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    telegram_app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    telegram_app.add_handler(
        MessageHandler(
            filters.TEXT &
            ~filters.COMMAND,
            message_handler
        )
    )


    telegram_app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    await telegram_app.initialize()


    await telegram_app.bot.delete_webhook()


    await telegram_app.bot.set_webhook(
        f"{RENDER_URL}/{BOT_TOKEN}"
    )


    await telegram_app.start()



def telegram_worker():

    global telegram_loop


    telegram_loop = asyncio.new_event_loop()

    asyncio.set_event_loop(
        telegram_loop
    )


    telegram_loop.run_until_complete(
        setup_bot()
    )


    telegram_loop.run_forever()



# =========================
# RUN
# =========================


if __name__ == "__main__":


    threading.Thread(
        target=telegram_worker,
        daemon=True
    ).start()



    app.run(
        host="0.0.0.0",
        port=PORT
    )
