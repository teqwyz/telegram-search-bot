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
    count_searches,
    count_today_searches,
    popular_queries,
    clear_history
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
# FLASK / RENDER
# =====================

app = Flask(
    __name__
)



@app.route("/")
def home():

    return "🤖 Smart Search Bot 2.4 Online"





def run_flask():

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )







# =====================
# РЕЖИМЫ ПОЛЬЗОВАТЕЛЕЙ
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
# SMART DETECT 2.4
# =====================

def smart_detect(text):

    t = text.lower()


    categories = {


        "music": [

            "песня",
            "трек",
            "музыка",
            "альбом",
            "слушать",
            "spotify",
            "mp3"

        ],


        "video": [

            "видео",
            "ютуб",
            "youtube",
            "фильм",
            "кино",
            "сериал"

        ],



        "shop": [

            "купить",
            "цена",
            "стоимость",
            "заказать",
            "товар",
            "магазин"

        ],



        "wiki": [

            "кто такой",
            "кто такая",
            "что такое",
            "история",
            "биография"

        ],



        "maps": [

            "где",
            "адрес",
            "рядом",
            "место",
            "карта"

        ],



        "news": [

            "новости",
            "события",
            "сейчас",
            "сегодня",
            "последние"

        ]

    }




    result = []



    for mode, words in categories.items():

        for word in words:

            if word in t:

                result.append(
                    mode
                )

                break





    return list(
        set(result)
    )










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
                "⬅ Назад",
                callback_data="menu"
            )

        ]

    ])







# =====================
# НАЗВАНИЯ РЕЖИМОВ
# =====================


MODE_NAMES = {


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

        "Я Smart Search Bot 2.4\n\n"

        "Возможности:\n\n"

        "🌐 Интернет\n"
        "🎵 Музыка\n"
        "🎬 Видео\n"
        "📚 Знания\n"
        "🛒 Товары\n"
        "🗺 Карты\n"
        "📰 Новости\n\n"

        "🧠 Умный поиск автоматически определяет категорию.\n\n"

        "Выбери режим:",

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

        "📌 Команды Smart Search Bot 2.4\n\n"

        "/start — открыть меню\n"
        "/help — помощь\n"
        "/about — информация\n"
        "/history — история поиска\n"
        "/news — новости\n"
        "/admin — админ панель\n\n"

        "Inline режим:\n"
        "@имя_бота запрос\n\n"

        "Пример:\n"
        "@SmartBot GTA 6"

    )









# =====================
# ABOUT
# =====================


async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):


    await update.message.reply_text(

        "🤖 Smart Search Bot 2.4\n\n"

        f"Создатель: {OWNER}\n\n"

        "Добавлено:\n\n"

        "✅ SQLite база\n"
        "✅ История поиска\n"
        "✅ Inline Mode\n"
        "✅ Новости\n"
        "✅ Админ статистика\n"
        "✅ Smart Detect\n"
        "✅ Популярные запросы\n\n"

        "Версия: 2.4"

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

            "⭐ История поиска пустая"

        )


        return





    text = "⭐ Последние запросы:\n\n"



    for i, item in enumerate(
        items,
        1
    ):

        text += f"{i}. {item}\n"





    await update.message.reply_text(
        text
    )









# =====================
# НОВОСТИ
# =====================


async def news_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):


    user_id = update.effective_user.id


    modes[
        user_id
    ] = "news"



    await update.message.reply_text(

        "📰 Режим новостей включён\n\n"

        "Напиши тему новости."

    )









# =====================
# CALLBACK КНОПКИ
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







    # Главное меню

    if data == "menu":


        modes[user_id] = "web"



        await query.edit_message_text(

            "🤖 Главное меню:",

            reply_markup=main_menu()

        )


        return







    # История

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







    # выбор режима


    modes[
        user_id
    ] = data



    await query.edit_message_text(

        "✅ Режим выбран:\n\n"

        f"{MODE_NAMES.get(data,'Поиск')}\n\n"

        "✏️ Напиши запрос",

        reply_markup=main_menu()

    )









# =====================
# МЕНЮ НОВОСТЕЙ
# =====================


def news_menu(text):


    q = encode(
        text
    )


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
# ПОИСКОВЫЕ МЕНЮ
# =====================


def search_buttons(text):

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








def shop_menu(text):

    q = encode(text)


    return InlineKeyboardMarkup([


        [

            InlineKeyboardButton(
                "🛒 Ozon",
                url=f"https://www.ozon.ru/search/?text={q}"
            )

        ],


        [

            InlineKeyboardButton(
                "🛒 Wildberries",
                url=f"https://www.wildberries.ru/catalog/0/search.aspx?search={q}"
            )

        ],


        [

            InlineKeyboardButton(
                "🛒 Яндекс Маркет",
                url=f"https://market.yandex.ru/search?text={q}"
            )

        ],


        [

            InlineKeyboardButton(
                "⬅ Меню",
                callback_data="menu"
            )

        ]

    ])








def maps_menu(text):

    q = encode(text)


    return InlineKeyboardMarkup([


        [

            InlineKeyboardButton(
                "🗺 Google Maps",
                url=f"https://www.google.com/maps/search/?api=1&query={q}"
            )

        ],


        [

            InlineKeyboardButton(
                "🗺 Яндекс Карты",
                url=f"https://yandex.ru/maps/?text={q}"
            )

        ],


        [

            InlineKeyboardButton(
                "🗺 2ГИС",
                url=f"https://2gis.ru/search/{q}"
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




    user = update.effective_user


    user_id = user.id



    # добавляем пользователя

    add_user(
        user
    )



    # сохраняем запрос

    add_history(
        user_id,
        text
    )



    mode = modes.get(
        user_id,
        "web"
    )





    # =====================
    # УМНЫЙ ПОИСК
    # =====================


    detected = smart_detect(
        text
    )



    if detected and mode == "web":


        buttons = []



        for item in detected:



            buttons.append(

                [

                    InlineKeyboardButton(

                        f"{MODE_NAMES[item]}",

                        callback_data=item

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

            "🧠 Найдены подходящие категории:",

            reply_markup=InlineKeyboardMarkup(buttons)

        )


        return







    # =====================
    # РЕЖИМЫ
    # =====================


    if mode == "web":


        await update.message.reply_text(

            "🌐 Интернет:",

            reply_markup=search_buttons(text)

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




    elif mode == "shop":


        await update.message.reply_text(

            "🛒 Товары:",

            reply_markup=shop_menu(text)

        )




    elif mode == "maps":


        await update.message.reply_text(

            "🗺 Карты:",

            reply_markup=maps_menu(text)

        )




    elif mode == "news":


        await update.message.reply_text(

            "📰 Новости:",

            reply_markup=news_menu(text)

        )




    elif mode == "wiki":


        q = encode(text)



        await update.message.reply_text(

            "📚 Знания:",

            reply_markup=InlineKeyboardMarkup([


                [

                    InlineKeyboardButton(

                        "📚 Википедия",

                        url=f"https://ru.wikipedia.org/wiki/{q}"

                    )

                ],


                [

                    InlineKeyboardButton(

                        "⬅ Меню",

                        callback_data="menu"

                    )

                ]

            ])

        )

# =====================
# INLINE MODE 2.4
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

            title="🔎 Поиск Google",

            description=query,

            input_message_content=

            InputTextMessageContent(

                f"https://www.google.com/search?q={q}"

            )

        ),



        InlineQueryResultArticle(

            id="youtube",

            title="▶ YouTube",

            description=query,

            input_message_content=

            InputTextMessageContent(

                f"https://youtube.com/results?search_query={q}"

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

        ),



        InlineQueryResultArticle(

            id="music",

            title="🎵 Музыка",

            description=query,

            input_message_content=

            InputTextMessageContent(

                f"https://music.yandex.ru/search?text={q}"

            )

        ),



        InlineQueryResultArticle(

            id="maps",

            title="🗺 Карты",

            description=query,

            input_message_content=

            InputTextMessageContent(

                f"https://www.google.com/maps/search/{q}"

            )

        )

    ]




    await update.inline_query.answer(

        results,

        cache_time=1

    )









# =====================
# ADMIN PANEL
# =====================


def admin_menu():

    return InlineKeyboardMarkup([


        [

            InlineKeyboardButton(

                "📊 Статистика",

                callback_data="admin_stats"

            )

        ],



        [

            InlineKeyboardButton(

                "🔥 Популярные запросы",

                callback_data="admin_popular"

            )

        ],



        [

            InlineKeyboardButton(

                "🗑 Очистить историю",

                callback_data="admin_clear"

            )

        ],



        [

            InlineKeyboardButton(

                "⬅ Назад",

                callback_data="menu"

            )

        ]

    ])








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





    await update.message.reply_text(

        "👑 Админ панель",

        reply_markup=admin_menu()

    )









async def admin_buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):


    query = update.callback_query


    await query.answer()



    user_id = query.from_user.id



    if user_id != ADMIN_ID:

        await query.edit_message_text(

            "⛔ Нет доступа"

        )

        return





    data = query.data





    if data == "admin_stats":


        await query.edit_message_text(

            "📊 Статистика\n\n"

            f"👤 Пользователи: {count_users()}\n"

            f"🔎 Всего поисков: {count_searches()}\n"

            f"📅 Сегодня: {count_today_searches()}",

            reply_markup=admin_menu()

        )





    elif data == "admin_popular":


        items = popular_queries()



        text = "🔥 Популярные запросы:\n\n"



        if not items:

            text += "Нет данных"

        else:

            for i,item in enumerate(items,1):

                text += f"{i}. {item}\n"





        await query.edit_message_text(

            text,

            reply_markup=admin_menu()

        )







    elif data == "admin_clear":


        clear_history()



        await query.edit_message_text(

            "🗑 История очищена",

            reply_markup=admin_menu()

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




    init_db()





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







    # кнопки


    application.add_handler(

        CallbackQueryHandler(
            buttons
        )

    )



    application.add_handler(

        CallbackQueryHandler(

            admin_buttons,

            pattern="^admin_"

        )

    )







    # inline


    application.add_handler(

        InlineQueryHandler(
            inline_search
        )

    )







    # текст


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

        "✅ Smart Search Bot 2.4 STARTED"

    )





    application.run_polling(

        drop_pending_updates=True

    )









# =====================
# MAIN
# =====================


if __name__ == "__main__":

    run()
