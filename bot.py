import os
import threading

from flask import Flask

from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)


from keyboards import (
    main_menu,
    settings_menu,
    web_buttons,
    music_buttons,
    video_buttons,
    shop_buttons,
    maps_buttons
)

from search import smart_search

from database import (
    create_user,
    add_history,
    get_history,
    get_favorites,
    clear_history
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





# =====================
# FLASK
# =====================

app = Flask(__name__)


@app.route("/")
def home():

    return "🤖 Smart Search Bot Online"





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

users = {}





# =====================
# СОЗДАНИЕ ПРОФИЛЯ
# =====================

def get_user(user_id):

    if user_id not in users:

        users[user_id] = {
            "mode": "web"
        }

    return users[user_id]





# =====================
# START
# =====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    create_user(user_id)

    users[user_id] = {
        "mode": "web"
    }


    await update.message.reply_text(

        "🤖 Добро пожаловать!\n\n"
        "Я Smart Search Bot 🔎\n\n"
        "Умею искать:\n\n"
        "🌐 Интернет\n"
        "🎵 Музыка\n"
        "🎬 Видео\n"
        "📚 Знания\n"
        "🛒 Покупки\n"
        "🗺 Карты\n\n"
        "Выбери категорию:",

        reply_markup=main_menu()

    )





# =====================
# ABOUT
# =====================

async def about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🤖 Smart Search Bot\n\n"
        f"Создатель: {OWNER}\n\n"

        "Возможности:\n"
        "🔎 Умный поиск без ИИ\n"
        "📊 История запросов\n"
        "⭐ Избранное\n"
        "⚙ Настройки\n\n"

        "Версия: 3.0"

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
        "/favorites — избранное"

    )





# =====================
# ИСТОРИЯ
# =====================

async def history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    items = get_history(user_id)


    if not items:

        await update.message.reply_text(
            "📊 История пустая"
        )

        return


    text = "📊 Последние запросы:\n\n"


    for i, item in enumerate(items, 1):

        text += f"{i}. {item}\n"


    await update.message.reply_text(text)





# =====================
# ИЗБРАННОЕ
# =====================

async def favorites(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    items = get_favorites(user_id)


    if not items:

        await update.message.reply_text(
            "⭐ Избранное пустое"
        )

        return


    text = "⭐ Избранное:\n\n"


    for item in items:

        text += f"• {item}\n"


    await update.message.reply_text(text)





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

    create_user(user_id)

    user = get_user(user_id)


    data = query.data





    # Главное меню

    if data == "menu":

        user["mode"] = "web"


        await query.edit_message_text(

            "🤖 Главное меню:",

            reply_markup=main_menu()

        )

        return





    # История

    if data == "history":

        items = get_history(user_id)


        if not items:

            text = "📊 История пустая"

        else:

            text = "📊 История:\n\n"

            for i,item in enumerate(items,1):

                text += f"{i}. {item}\n"


        await query.edit_message_text(

            text,

            reply_markup=main_menu()

        )

        return





    # Настройки

    if data == "settings":

        await query.edit_message_text(

            "⚙ Настройки",

            reply_markup=settings_menu()

        )

        return





    # Очистка истории

    if data == "clear_history":

        clear_history(user_id)


        await query.edit_message_text(

            "🧹 История очищена",

            reply_markup=main_menu()

        )

        return





    # Выбор режима

    if data in [

        "web",
        "music",
        "video",
        "wiki",
        "shop",
        "maps"

    ]:

        user["mode"] = data


        await query.edit_message_text(

            f"✅ Выбран режим:\n\n"
            f"{data}\n\n"
            "Отправь запрос",

            reply_markup=main_menu()

        )

        return

# =====================
# СООБЩЕНИЯ
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


    create_user(user_id)


    user = get_user(user_id)


    mode = user["mode"]



    # сохраняем историю

    add_history(
        user_id,
        text
    )



    # умный анализ запроса

    result = smart_search(text)



    category = result["category"]



    # если выбран обычный интернет,
    # разрешаем автоопределение

    if mode == "web":

        mode = category



    query = result["query"]



    keyboard = None



    # =====================
    # ВЫБОР ПОИСКА
    # =====================


    if mode == "web":

        keyboard = web_buttons(
            query
        )

        title = "🌐 Интернет"


    elif mode == "music":

        keyboard = music_buttons(
            query
        )

        title = "🎵 Музыка"


    elif mode == "video":

        keyboard = video_buttons(
            query
        )

        title = "🎬 Видео"


    elif mode == "shop":

        keyboard = shop_buttons(
            query
        )

        title = "🛒 Покупки"


    elif mode == "maps":

        keyboard = maps_buttons(
            query
        )

        title = "🗺 Карты"



    elif mode == "wiki":

        await update.message.reply_text(

            "📚 Найдено:\n\n"
            f"{result['text']}"

        )

        return



    else:

        keyboard = web_buttons(
            query
        )

        title = "🌐 Интернет"




    await update.message.reply_text(

        f"{title}\n\n"
        f"🔎 Запрос:\n{query}\n\n"
        "Выбери сервис:",

        reply_markup=keyboard

    )





# =====================
# ERROR
# =====================

async def error_handler(
    update,
    context
):

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
            "BOT_TOKEN отсутствует"
        )



    # Flask для Render

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





    # =====================
    # КОМАНДЫ
    # =====================


    bot.add_handler(

        CommandHandler(
            "start",
            start
        )

    )


    bot.add_handler(

        CommandHandler(
            "help",
            help_command
        )

    )


    bot.add_handler(

        CommandHandler(
            "about",
            about
        )

    )


    bot.add_handler(

        CommandHandler(
            "history",
            history
        )

    )


    bot.add_handler(

        CommandHandler(
            "favorites",
            favorites
        )

    )





    # =====================
    # КНОПКИ
    # =====================


    bot.add_handler(

        CallbackQueryHandler(
            buttons
        )

    )





    # =====================
    # ТЕКСТ
    # =====================


    bot.add_handler(

        MessageHandler(

            filters.TEXT &
            ~filters.COMMAND,

            message

        )

    )





    bot.add_error_handler(

        error_handler

    )





    print(
        "✅ SMART SEARCH BOT STARTED"
    )





    bot.run_polling()





# =====================
# MAIN
# =====================

if __name__ == "__main__":

    run()

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from urllib.parse import quote





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

        ],



        [

            InlineKeyboardButton(
                "⭐ История",
                callback_data="history"
            ),

            InlineKeyboardButton(
                "⚙ Настройки",
                callback_data="settings"
            )

        ]

    ])







# =====================
# НАСТРОЙКИ
# =====================

def settings_menu():

    return InlineKeyboardMarkup([


        [

            InlineKeyboardButton(
                "🧹 Очистить историю",
                callback_data="clear_history"
            )

        ],



        [

            InlineKeyboardButton(
                "⭐ Избранное",
                callback_data="favorites"
            )

        ],



        [

            InlineKeyboardButton(
                "⬅ Главное меню",
                callback_data="menu"
            )

        ]

    ])







# =====================
# НАЗАД
# =====================

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
# ИНТЕРНЕТ
# =====================

def web_buttons(query):

    q = quote(query)


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

def music_buttons(query):

    q = quote(query)


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

def video_buttons(query):

    q = quote(query)


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
                "⬅ Меню",
                callback_data="menu"
            )

        ]

    ])







# =====================
# ПОКУПКИ
# =====================

def shop_buttons(query):

    q = quote(query)


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







# =====================
# КАРТЫ
# =====================

def maps_buttons(query):

    q = quote(query)


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
# SMART SEARCH ENGINE
# Без ИИ
# =====================


# =====================
# КАТЕГОРИИ
# =====================

CATEGORIES = {


    "music": [

        "песня",
        "трек",
        "музыка",
        "альбом",
        "исполнитель",
        "певец",
        "певица",
        "слушать",
        "lyrics",
        "song",
        "spotify"

    ],



    "video": [

        "фильм",
        "кино",
        "сериал",
        "трейлер",
        "ютуб",
        "youtube",
        "видео",
        "смотреть",
        "обзор",
        "клип"

    ],



    "shop": [

        "купить",
        "цена",
        "стоимость",
        "заказать",
        "магазин",
        "доставка",
        "ozon",
        "озон",
        "wildberries",
        "вб",
        "iphone",
        "айфон",
        "телефон"

    ],



    "maps": [

        "адрес",
        "где находится",
        "карта",
        "улица",
        "метро",
        "маршрут",
        "как доехать",
        "рядом"

    ],



    "wiki": [

        "кто",
        "что такое",
        "история",
        "биография",
        "почему",
        "объясни",
        "значение",
        "когда появился"

    ]

}





# =====================
# ОЧИСТКА ТЕКСТА
# =====================

def normalize(text):

    if not text:
        return ""

    return (
        text
        .lower()
        .replace("ё", "е")
        .strip()
    )







# =====================
# ОПРЕДЕЛЕНИЕ КАТЕГОРИИ
# =====================

def detect_category(text):

    text = normalize(text)


    scores = {

        "music": 0,
        "video": 0,
        "shop": 0,
        "maps": 0,
        "wiki": 0

    }



    for category, words in CATEGORIES.items():

        for word in words:

            if word in text:

                scores[category] += 1






    best = max(
        scores,
        key=scores.get
    )



    if scores[best] == 0:

        return "web"



    return best







# =====================
# НАЗВАНИЕ
# =====================

def category_title(category):

    titles = {


        "web":
        "🌐 Интернет",


        "music":
        "🎵 Музыка",


        "video":
        "🎬 Видео",


        "shop":
        "🛒 Покупки",


        "maps":
        "🗺 Карты",


        "wiki":
        "📚 Знания"

    }


    return titles.get(
        category,
        "🌐 Интернет"
    )







# =====================
# ОТВЕТ
# =====================

def make_answer(text, category):


    if category == "wiki":

        return (

            "📚 Поиск знаний\n\n"
            f"Запрос:\n{text}\n\n"
            "Я нашёл направление поиска."

        )



    return (

        f"Категория: "
        f"{category_title(category)}\n\n"
        f"Запрос:\n{text}"

    )







# =====================
# ОСНОВНОЙ ПОИСК
# =====================

def smart_search(text):


    if not text:

        text = "пустой запрос"



    category = detect_category(text)



    return {


        "query":
            text,



        "category":
            category,



        "title":
            category_title(category),



        "text":
            make_answer(
                text,
                category
            )

    }
