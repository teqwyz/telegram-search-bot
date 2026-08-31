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
    add_favorite,
    get_favorites
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
        "Я Smart Search Bot 🔎\n"
        "Умею искать без ИИ:\n\n"
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
        "Функции:\n"
        "🔎 умный поиск\n"
        "📚 база знаний\n"
        "⭐ история\n"
        "⚙ настройки\n\n"
        "Работает без нейросетей."

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

        "/start — главное меню\n"
        "/help — помощь\n"
        "/about — информация\n"
        "/history — история поиска\n"
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
            "📊 История пуста"
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


    create_user(user_id)


    data = query.data



    if user_id not in users:

        users[user_id] = {
            "mode": "web"
        }



    if data == "menu":

        users[user_id]["mode"] = "web"


        await query.edit_message_text(

            "🤖 Главное меню:",

            reply_markup=main_menu()

        )

        return



    if data == "settings":

        await query.edit_message_text(

            "⚙ Настройки",

            reply_markup=settings_menu()

        )

        return



    if data in [

        "web",
        "music",
        "video",
        "wiki",
        "shop",
        "maps"

    ]:

        users[user_id]["mode"] = data


        await query.edit_message_text(

            f"✅ Режим выбран:\n\n"
            f"{data}\n\n"
            "Отправь запрос.",

            reply_markup=main_menu()

        )



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



    if user_id not in users:

        users[user_id] = {
            "mode": "web"
        }



    mode = users[user_id]["mode"]



    add_history(
        user_id,
        text
    )


    result = smart_search(text)



    query = result["query"]



    if mode == "web":

        keyboard = web_buttons(query)


    elif mode == "music":

        keyboard = music_buttons(query)


    elif mode == "video":

        keyboard = video_buttons(query)


    elif mode == "shop":

        keyboard = shop_buttons(query)


    elif mode == "maps":

        keyboard = maps_buttons(query)


    else:

        await update.message.reply_text(

            "📚 Найдено:\n\n"
            + result["text"]

        )

        return



    await update.message.reply_text(

        f"{result['title']}\n\n"
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
# RUN
# =====================

def run():


    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN отсутствует"
        )



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


    bot.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )


    bot.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message
        )
    )


    bot.add_error_handler(
        error_handler
    )


    print(
        "✅ BOT STARTED"
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
# ИНТЕРНЕТ
# =====================

def web_buttons(query):

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "🔎 Google",
                url=f"https://www.google.com/search?q={query}"
            )

        ],

        [

            InlineKeyboardButton(
                "🔎 Яндекс",
                url=f"https://yandex.ru/search/?text={query}"
            )

        ],

        [

            InlineKeyboardButton(
                "🔎 Bing",
                url=f"https://www.bing.com/search?q={query}"
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

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "🎵 Spotify",
                url=f"https://open.spotify.com/search/{query}"
            )

        ],

        [

            InlineKeyboardButton(
                "🎵 Яндекс Музыка",
                url=f"https://music.yandex.ru/search?text={query}"
            )

        ],

        [

            InlineKeyboardButton(
                "🎵 VK Музыка",
                url=f"https://vk.com/audio?section=search&q={query}"
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

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "▶ YouTube",
                url=f"https://www.youtube.com/results?search_query={query}"
            )

        ],

        [

            InlineKeyboardButton(
                "▶ VK Видео",
                url=f"https://vk.com/video?q={query}"
            )

        ],

        [

            InlineKeyboardButton(
                "▶ Rutube",
                url=f"https://rutube.ru/search/?query={query}"
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

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "🛒 Ozon",
                url=f"https://www.ozon.ru/search/?text={query}"
            )

        ],

        [

            InlineKeyboardButton(
                "🛒 Wildberries",
                url=f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
            )

        ],

        [

            InlineKeyboardButton(
                "🛒 Яндекс Маркет",
                url=f"https://market.yandex.ru/search?text={query}"
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

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "🗺 Google Maps",
                url=f"https://www.google.com/maps/search/?api=1&query={query}"
            )

        ],

        [

            InlineKeyboardButton(
                "🗺 Яндекс Карты",
                url=f"https://yandex.ru/maps/?text={query}"
            )

        ],

        [

            InlineKeyboardButton(
                "🗺 2ГИС",
                url=f"https://2gis.ru/search/{query}"
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
        "текст песни",
        "lyrics",
        "song",
        "spotify"

    ],



    "video": [

        "фильм",
        "кино",
        "сериал",
        "мультфильм",
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
        "ноутбук",
        "телефон"

    ],



    "maps": [

        "адрес",
        "где находится",
        "найти",
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
# АНАЛИЗ ЗАПРОСА
# =====================

def smart_search(text):


    category = detect_category(text)



    return {


        "query": text,


        "category": category,


        "title": category_title(category),


        "text":
            make_answer(
                text,
                category
            )

    }





# =====================
# ОТВЕТ ДЛЯ WIKI
# =====================

def make_answer(
    text,
    category
):


    if category == "wiki":

        return (

            "Я определил запрос как "
            "запрос знаний.\n\n"
            f"🔎 Поиск информации:\n{text}"

        )



    return (

        "Категория:\n"
        f"{category_title(category)}\n\n"
        f"Запрос: {text}"

    )

import os
import json
from datetime import datetime



# =====================
# НАСТРОЙКИ
# =====================

DATA_FOLDER = "data"

DATABASE_FILE = os.path.join(
    DATA_FOLDER,
    "users.json"
)





# =====================
# СОЗДАНИЕ БАЗЫ
# =====================

def init_database():

    if not os.path.exists(DATA_FOLDER):

        os.makedirs(
            DATA_FOLDER
        )


    if not os.path.exists(DATABASE_FILE):

        with open(
            DATABASE_FILE,
            "w",
            encoding="utf-8"
        ) as file:


            json.dump(

                {},

                file,

                ensure_ascii=False,

                indent=4

            )





# =====================
# ЗАГРУЗКА
# =====================

def load_database():

    init_database()


    with open(
        DATABASE_FILE,
        "r",
        encoding="utf-8"
    ) as file:


        return json.load(file)





# =====================
# СОХРАНЕНИЕ
# =====================

def save_database(data):

    with open(
        DATABASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:


        json.dump(

            data,

            file,

            ensure_ascii=False,

            indent=4

        )





# =====================
# СОЗДАТЬ ПОЛЬЗОВАТЕЛЯ
# =====================

def create_user(user_id):

    data = load_database()


    user_id = str(user_id)



    if user_id not in data:


        data[user_id] = {


            "history": [],


            "favorites": [],


            "created": str(
                datetime.now()
            )


        }


        save_database(data)





# =====================
# ДОБАВИТЬ ИСТОРИЮ
# =====================

def add_history(
    user_id,
    query
):

    create_user(
        user_id
    )


    data = load_database()


    user_id = str(user_id)



    history = data[user_id]["history"]



    if query in history:

        history.remove(query)



    history.insert(
        0,
        query
    )



    data[user_id]["history"] = history[:30]



    save_database(data)





# =====================
# ПОЛУЧИТЬ ИСТОРИЮ
# =====================

def get_history(user_id):

    data = load_database()


    user_id = str(user_id)



    if user_id not in data:

        return []



    return data[user_id].get(

        "history",

        []

    )





# =====================
# ДОБАВИТЬ В ИЗБРАННОЕ
# =====================

def add_favorite(
    user_id,
    query
):

    create_user(
        user_id
    )


    data = load_database()


    user_id = str(user_id)



    favorites = data[user_id]["favorites"]



    if query not in favorites:


        favorites.append(
            query
        )



    data[user_id]["favorites"] = favorites[:50]



    save_database(data)





# =====================
# ПОЛУЧИТЬ ИЗБРАННОЕ
# =====================

def get_favorites(user_id):

    data = load_database()


    user_id = str(user_id)



    if user_id not in data:

        return []



    return data[user_id].get(

        "favorites",

        []

    )





# =====================
# УДАЛИТЬ ИЗ ИЗБРАННОГО
# =====================

def remove_favorite(
    user_id,
    query
):

    data = load_database()


    user_id = str(user_id)



    if user_id in data:


        favorites = data[user_id]["favorites"]



        if query in favorites:


            favorites.remove(
                query
            )


            save_database(data)





# =====================
# СТАТИСТИКА
# =====================

def get_stats(user_id):

    data = load_database()


    user_id = str(user_id)



    if user_id not in data:

        return {

            "history": 0,

            "favorites": 0

        }



    return {


        "history":

            len(
                data[user_id]["history"]
            ),


        "favorites":

            len(
                data[user_id]["favorites"]
            )


    }
