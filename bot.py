import os
import threading
import requests

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ContextTypes,
    filters
)


from database import (
    init_db,
    add_user,
    add_history,
    get_history,
    count_users,
    count_searches
)



# =====================
# НАСТРОЙКИ
# =====================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)


PORT = int(
    os.getenv(
        "PORT",
        "10000"
    )
)


OWNER = "@teqwyz"


ADMIN_ID = int(
    os.getenv(
        "ADMIN_ID",
        "0"
    )
)



# =====================
# FLASK
# =====================

app = Flask(
    __name__
)



@app.route("/")
def home():

    return "🤖 Smart Search Bot 2.3 Online"




def run_flask():

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )





# =====================
# ПАМЯТЬ РЕЖИМОВ
# =====================

modes = {}





# =====================
# URL
# =====================

def encode(text):

    return requests.utils.quote(
        text,
        safe=""
    )





# =====================
# МЕНЮ
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
                "📰 Новости",
                callback_data="news"
            )

        ],


        [

            InlineKeyboardButton(
                "⭐ История",
                callback_data="history"
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
# START
# =====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    add_user(
        user
    )


    modes[
        user.id
    ] = "web"



    await update.message.reply_text(

        "🤖 Добро пожаловать!\n\n"

        "Я Smart Search Bot 2.3\n\n"

        "Возможности:\n\n"

        "🌐 Интернет\n"
        "🎵 Музыка\n"
        "🎬 Видео\n"
        "📚 Знания\n"
        "🛒 Товары\n"
        "🗺 Карты\n"
        "📰 Новости\n\n"

        "Выбери категорию:",

        reply_markup=main_menu()

    )





# =====================
# ABOUT
# =====================

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🤖 Smart Search Bot 2.3\n\n"

        f"Создатель: {OWNER}\n\n"

        "Добавлено:\n"

        "✅ SQLite база\n"
        "✅ История поиска\n"
        "✅ Inline режим\n"
        "✅ Новости\n"
        "✅ Статистика\n"

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
        "/history — история\n"
        "/news — новости\n"
        "/admin — статистика"

    )





# =====================
# ИСТОРИЯ
# =====================

async def history_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id


    items = get_history(
        user_id
    )


    if not items:

        await update.message.reply_text(
            "⭐ История пустая"
        )

        return



    text = "⭐ История поиска:\n\n"


    for i,item in enumerate(
        items,
        1
    ):

        text += f"{i}. {item}\n"



    await update.message.reply_text(
        text
    )





# =====================
# NEWS
# =====================

async def news_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    modes[
        update.effective_user.id
    ] = "news"


    await update.message.reply_text(

        "📰 Режим новостей включён\n\n"
        "Напиши тему поиска"

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


    user_id = query.from_user.id


    data = query.data



    if data == "menu":

        modes[user_id] = "web"


        await query.edit_message_text(

            "🤖 Главное меню:",

            reply_markup=main_menu()

        )

        return




    if data == "history":

        items = get_history(
            user_id
        )


        if not items:

            await query.edit_message_text(
                "⭐ История пустая",
                reply_markup=back_button()
            )

            return



        text = "⭐ История:\n\n"


        for i,item in enumerate(
            items,
            1
        ):

            text += f"{i}. {item}\n"



        await query.edit_message_text(

            text,

            reply_markup=back_button()

        )


        return





    modes[user_id] = data



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
        "🛒 Товары",

        "maps":
        "🗺 Карты",

        "news":
        "📰 Новости"

    }



    await query.edit_message_text(

        "✅ Выбран режим:\n\n"

        f"{names.get(data,'Поиск')}\n\n"

        "✏️ Напиши запрос",

        reply_markup=main_menu()

    )





# =====================
# НОВОСТИ КНОПКИ
# =====================

def news_menu(text):

    q = encode(text)


    return InlineKeyboardMarkup([


        [

            InlineKeyboardButton(

                "📰 Google News",

                url=
                f"https://news.google.com/search?q={q}"

            )

        ],


        [

            InlineKeyboardButton(

                "📰 Яндекс Новости",

                url=
                f"https://yandex.ru/news/search?text={q}"

            )

        ],


        [

            InlineKeyboardButton(

                "🔎 Bing News",

                url=
                f"https://www.bing.com/news/search?q={q}"

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
# ОБРАБОТКА СООБЩЕНИЙ
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



    user = update.effective_user


    user_id = user.id



    add_user(
        user
    )


    add_history(

        user_id,

        text

    )



    mode = modes.get(

        user_id,

        "web"

    )





    if mode == "news":

        await update.message.reply_text(

            "📰 Новости:",

            reply_markup=news_menu(text)

        )

        return





    if mode == "web":

        await update.message.reply_text(

            "🌐 Поиск:",

            reply_markup=InlineKeyboardMarkup([


                [

                    InlineKeyboardButton(

                        "🔎 Google",

                        url=
                        f"https://www.google.com/search?q={encode(text)}"

                    )

                ],


                [

                    InlineKeyboardButton(

                        "🔎 Яндекс",

                        url=
                        f"https://yandex.ru/search/?text={encode(text)}"

                    )

                ],


                [

                    InlineKeyboardButton(

                        "🔎 Bing",

                        url=
                        f"https://www.bing.com/search?q={encode(text)}"

                    )

                ]


            ])

        )



    elif mode == "music":


        await update.message.reply_text(

            "🎵 Музыка:",

            reply_markup=InlineKeyboardMarkup([


                [

                    InlineKeyboardButton(

                        "Spotify",

                        url=
                        f"https://open.spotify.com/search/{encode(text)}"

                    )

                ],


                [

                    InlineKeyboardButton(

                        "Яндекс Музыка",

                        url=
                        f"https://music.yandex.ru/search?text={encode(text)}"

                    )

                ]


            ])

        )





    elif mode == "video":


        await update.message.reply_text(

            "🎬 Видео:",

            reply_markup=InlineKeyboardMarkup([


                [

                    InlineKeyboardButton(

                        "▶ YouTube",

                        url=
                        f"https://youtube.com/results?search_query={encode(text)}"

                    )

                ],


                [

                    InlineKeyboardButton(

                        "▶ VK Видео",

                        url=
                        f"https://vk.com/video?q={encode(text)}"

                    )

                ]


            ])

        )





    else:


        await update.message.reply_text(

            "🔎 Поиск:",

            reply_markup=InlineKeyboardMarkup([


                [

                    InlineKeyboardButton(

                        "Открыть поиск",

                        url=
                        f"https://www.google.com/search?q={encode(text)}"

                    )

                ]


            ])

        )





# =====================
# INLINE SEARCH
# =====================

async def inline_search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.inline_query.query


    if not query:

        return



    q = encode(query)



    results = [


        InlineQueryResultArticle(

            id="google",

            title="🔎 Google",

            description=query,

            input_message_content=

            InputTextMessageContent(

                f"https://www.google.com/search?q={q}"

            )

        ),



        InlineQueryResultArticle(

            id="news",

            title="📰 Новости",

            description=query,

            input_message_content=

            InputTextMessageContent(

                f"https://news.google.com/search?q={q}"

            )

        )

    ]



    await update.inline_query.answer(

        results,

        cache_time=1

    )

# =====================
# ADMIN
# =====================

async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id


    if user_id != ADMIN_ID:

        await update.message.reply_text(
            "⛔ Нет доступа"
        )

        return



    users_count = count_users()

    searches_count = count_searches()



    await update.message.reply_text(

        "👑 Админ статистика\n\n"

        f"👤 Пользователей: {users_count}\n"

        f"🔎 Поисков: {searches_count}\n\n"

        "🤖 Smart Search Bot 2.3"

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
            "BOT_TOKEN отсутствует"
        )



    # создаём SQLite

    init_db()



    # запускаем Flask для Render

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
            "history",
            history_command
        )

    )


    application.add_handler(

        CommandHandler(
            "news",
            news_command
        )

    )


    application.add_handler(

        CommandHandler(
            "admin",
            admin_command
        )

    )





    # =====================
    # CALLBACK BUTTONS
    # =====================


    application.add_handler(

        CallbackQueryHandler(
            buttons
        )

    )





    # =====================
    # INLINE MODE
    # =====================


    application.add_handler(

        InlineQueryHandler(
            inline_search
        )

    )





    # =====================
    # TEXT
    # =====================


    application.add_handler(

        MessageHandler(

            filters.TEXT
            &
            ~filters.COMMAND,

            message

        )

    )





    application.add_error_handler(

        error_handler

    )





    print(
        "✅ Smart Search Bot 2.3 STARTED"
    )





    application.run_polling(

        drop_pending_updates=True

    )





# =====================
# MAIN
# =====================

if __name__ == "__main__":

    run()
