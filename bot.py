import json
import os
from datetime import datetime


# =====================
# НАСТРОЙКИ БАЗЫ
# =====================

DATA_FOLDER = "data"

DATABASE_FILE = os.path.join(
    DATA_FOLDER,
    "users.json"
)


# =====================
# СОЗДАНИЕ ПАПКИ
# =====================

def init_database():

    if not os.path.exists(DATA_FOLDER):

        os.makedirs(DATA_FOLDER)


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
# СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ
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
# ДОБАВИТЬ В ИСТОРИЮ
# =====================

def add_history(
    user_id,
    query
):

    data = load_database()


    user_id = str(user_id)


    create_user(user_id)


    data = load_database()


    history = data[user_id]["history"]


    history.insert(
        0,
        query
    )


    # максимум 20 запросов

    data[user_id]["history"] = history[:20]


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

    data = load_database()


    user_id = str(user_id)


    create_user(user_id)


    data = load_database()


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

        if query in data[user_id]["favorites"]:

            data[user_id]["favorites"].remove(
                query
            )


            save_database(data)

# =====================
# SEARCH ENGINE 3.0
# Умный поиск без ИИ
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
        "song"

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
        "wildberries",
        "айфон",
        "iphone",
        "ноутбук"

    ],


    "maps": [

        "адрес",
        "где находится",
        "найти",
        "карта",
        "улица",
        "метро",
        "как доехать",
        "маршрут"

    ],


    "wiki": [

        "кто",
        "что такое",
        "история",
        "биография",
        "почему",
        "объясни",
        "значение"

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





    result = max(

        scores,

        key=scores.get

    )





    # если совпадений нет

    if scores[result] == 0:

        return "web"



    return result





# =====================
# КРАСИВОЕ НАЗВАНИЕ
# =====================

def category_name(category):


    names = {


        "web":

        "🌐 Интернет",


        "music":

        "🎵 Музыка",


        "video":

        "🎬 Видео",


        "shop":

        "🛒 Товары",


        "maps":

        "🗺 Карты",


        "wiki":

        "📚 Знания"

    }



    return names.get(

        category,

        "🌐 Интернет"

    )





# =====================
# АНАЛИЗ ЗАПРОСА
# =====================

def analyze_query(text):


    category = detect_category(text)



    return {


        "query": text,


        "category": category,


        "title":

            category_name(category)

    }

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
                "⭐ Избранное",
                callback_data="favorites"
            ),

            InlineKeyboardButton(
                "📊 Статистика",
                callback_data="stats"
            )

        ],


        [

            InlineKeyboardButton(
                "⚙ Настройки",
                callback_data="settings"
            )

        ]

    ])





# =====================
# КНОПКА НАЗАД
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
# ПОИСКОВИКИ
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
                url=f"https://youtube.com/results?search_query={query}"
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
# ТОВАРЫ
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
# НАСТРОЙКИ
# =====================

def settings_menu():

    return InlineKeyboardMarkup([


        [

            InlineKeyboardButton(
                "🔔 Уведомления",
                callback_data="notifications"
            )

        ],


        [

            InlineKeyboardButton(
                "🧹 Очистить историю",
                callback_data="clear"
            )

        ],


        [

            InlineKeyboardButton(
                "⬅ Главное меню",
                callback_data="menu"
            )

        ]

    ])

import os
import threading
import requests

from flask import Flask

from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)


from keyboards import (
    main_menu,
    web_buttons,
    music_buttons,
    video_buttons,
    shop_buttons,
    maps_buttons,
    settings_menu
)


from search import smart_search





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


users = {}





# =====================
# RENDER
# =====================

@app.route("/")
def home():

    return "🤖 Search Bot Online"




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
# START
# =====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user.id


    users[user] = {

        "mode": "web",
        "history": []

    }


    await update.message.reply_text(

        "🤖 Добро пожаловать!\n\n"
        "Я умный поисковый бот.\n"
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

        "🤖 Search Bot\n\n"
        f"Создатель: {OWNER}\n\n"

        "Возможности:\n"
        "🌐 Интернет\n"
        "🎵 Музыка\n"
        "🎬 Видео\n"
        "📚 Знания\n"
        "🛒 Покупки\n"
        "🗺 Карты\n\n"

        "Работает без нейросетей."

    )





# =====================
# BUTTONS
# =====================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    if not query:
        return


    await query.answer()



    user = query.from_user.id


    data = query.data



    if user not in users:

        users[user] = {

            "mode":"web",
            "history":[]

        }





    if data == "menu":


        users[user]["mode"] = "web"


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


        users[user]["mode"] = data



        names = {

            "web":"🌐 Интернет",
            "music":"🎵 Музыка",
            "video":"🎬 Видео",
            "wiki":"📚 Знания",
            "shop":"🛒 Покупки",
            "maps":"🗺 Карты"

        }



        await query.edit_message_text(

            f"✅ Выбрано:\n\n"
            f"{names[data]}\n\n"
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



    user = update.effective_user.id



    if user not in users:

        users[user] = {

            "mode":"web",
            "history":[]

        }




    mode = users[user]["mode"]




    # сохраняем историю

    users[user]["history"].append(text)



    q = encode(text)



    result = smart_search(text)





    if mode == "web":

        await update.message.reply_text(

            "🌐 Поиск:",

            reply_markup=web_buttons(q)

        )



    elif mode == "music":


        await update.message.reply_text(

            "🎵 Музыка:",

            reply_markup=music_buttons(q)

        )




    elif mode == "video":


        await update.message.reply_text(

            "🎬 Видео:",

            reply_markup=video_buttons(q)

        )





    elif mode == "shop":


        await update.message.reply_text(

            "🛒 Магазины:",

            reply_markup=shop_buttons(q)

        )





    elif mode == "maps":


        await update.message.reply_text(

            "🗺 Карты:",

            reply_markup=maps_buttons(q)

        )





    else:


        await update.message.reply_text(

            "📚 Результат:\n\n"
            + result

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
        "/about — информация\n"
        "/help — помощь"

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



    bot.add_error_handler(
        error_handler
    )



    print(
        "✅ BOT STARTED"
    )



    bot.run_polling()






if __name__ == "__main__":

    run()
