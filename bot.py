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


# режимы пользователей

modes = {}


# история запросов

history = {}



# избранное

favorites = {}





# =====================
# FLASK / RENDER
# =====================

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
# URL
# =====================

def encode(text):

    return requests.utils.quote(

        text,

        safe=""

    )





# =====================
# ИСПРАВЛЕНИЕ ОПЕЧАТОК
# =====================

REPLACE_WORDS = {


    "ютуб":
    "youtube",


    "ютубе":
    "youtube",


    "ютубчик":
    "youtube",


    "айфон":
    "iphone",


    "афон":
    "iphone",


    "озон":
    "ozon",


    "озончик":
    "ozon",


    "вк":
    "vk"

}





def fix_text(text):

    text = text.lower()



    for old, new in REPLACE_WORDS.items():

        text = text.replace(

            old,

            new

        )



    return text





# =====================
# УМНЫЙ ПОИСК
# =====================


SEARCH_RULES = {


    "music": [

        "песня",

        "трек",

        "альбом",

        "исполнитель",

        "музыка",

        "слушать"

    ],



    "video": [

        "фильм",

        "сериал",

        "видео",

        "youtube",

        "трейлер",

        "смотреть"

    ],



    "shop": [

        "купить",

        "цена",

        "стоимость",

        "заказать",

        "магазин",

        "руб",

        "iphone",

        "ozon"

    ],



    "wiki": [

        "кто",

        "что такое",

        "история",

        "биография",

        "значение"

    ],



    "maps": [

        "где",

        "адрес",

        "рядом",

        "место",

        "найти"

    ]

}






def smart_search(text):


    text = fix_text(text)



    scores = {}



    for mode, words in SEARCH_RULES.items():

        score = 0



        for word in words:

            if word in text:

                score += 1



        scores[mode] = score




    result = sorted(

        scores,

        key=scores.get,

        reverse=True

    )



    found = []



    for mode in result:

        if scores[mode] > 0:

            found.append(mode)



    if not found:

        return [

            "web"

        ]



    return found





# =====================
# НАЗВАНИЯ КАТЕГОРИЙ
# =====================


CATEGORY_NAMES = {


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





def category_text(categories):


    result = []



    for item in categories:

        result.append(

            CATEGORY_NAMES.get(

                item,

                item

            )

        )



    return "\n".join(result)





# =====================
# СОХРАНЕНИЕ ИСТОРИИ
# =====================


def add_history(
    user_id,
    text
):


    if user_id not in history:

        history[user_id] = []



    history[user_id].insert(

        0,

        text

    )



    history[user_id] = history[user_id][:10]





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
# КНОПКА НАЗАД
# =====================

def back_button():

    return [

        InlineKeyboardButton(

            "⬅ Главное меню",

            callback_data="menu"

        )

    ]





# =====================
# WEB ПОИСК
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


        back_button()

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


        back_button()

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

        ],


        back_button()

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


        buttons.append([


            InlineKeyboardButton(

                name,

                url=url

            )


        ])




    buttons.append(

        back_button()

    )



    return InlineKeyboardMarkup(buttons)





# =====================
# КРАСИВАЯ КАРТОЧКА
# =====================

def result_card(
    text,
    categories
):


    return (

        "╭━━━━━━━━━━━━╮\n"

        " 🧠 SMART SEARCH\n"

        "╰━━━━━━━━━━━━╯\n\n"

        f"🔎 Запрос:\n"
        f"{text}\n\n"

        "📂 Найдено:\n"

        f"{category_text(categories)}\n\n"

        "Выберите действие 👇"

    )





# =====================
# ПОКАЗ НЕСКОЛЬКИХ КАТЕГОРИЙ
# =====================

def multi_menu(
    text,
    categories
):


    buttons = []



    for category in categories:


        buttons.append([


            InlineKeyboardButton(

                CATEGORY_NAMES[category],

                callback_data=f"search_{category}"

            )


        ])



    buttons.append(

        back_button()

    )


    return InlineKeyboardMarkup(buttons)





# =====================
# ИЗБРАННОЕ
# =====================

def add_favorite(
    user_id,
    site
):


    if user_id not in favorites:

        favorites[user_id] = []



    if site not in favorites[user_id]:

        favorites[user_id].append(site)





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




    if data == "menu":


        await query.edit_message_text(

            "🤖 Главное меню\n\n"
            "Выберите режим:",

            reply_markup=main_menu()

        )


        return





    if data.startswith("search_"):


        mode = data.replace(

            "search_",

            ""

        )


        context.user_data["last_mode"] = mode



        await query.edit_message_text(

            f"✅ Выбрано:\n\n"
            f"{CATEGORY_NAMES[mode]}\n\n"
            "Отправьте запрос ещё раз."

        )


        return





    modes[user_id] = data



    await query.edit_message_text(

        "✅ Режим установлен:\n\n"

        f"{CATEGORY_NAMES.get(data)}\n\n"

        "✏️ Отправьте запрос",

        reply_markup=main_menu()

    )

# =====================
# START
# =====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    modes[user_id] = "web"


    await update.message.reply_text(

        "╭━━━━━━━━━━━━╮\n"
        " 🤖 SMART SEARCH\n"
        "╰━━━━━━━━━━━━╯\n\n"

        "Я умный поисковый бот.\n"
        "Без нейросетей — только анализ запроса.\n\n"

        "Выберите категорию:",

        reply_markup=main_menu()

    )





# =====================
# HISTORY
# =====================

async def history_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id


    items = history.get(
        user_id,
        []
    )


    if not items:

        await update.message.reply_text(

            "📜 История пока пустая."

        )

        return



    text = "📜 Последние запросы:\n\n"



    for i, item in enumerate(
        items,
        1
    ):

        text += f"{i}. {item}\n"



    await update.message.reply_text(text)





# =====================
# FAVORITE
# =====================

async def favorite_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id


    items = favorites.get(

        user_id,

        []

    )


    if not items:


        await update.message.reply_text(

            "⭐ Избранное пустое."

        )


        return



    text = "⭐ Избранные сайты:\n\n"


    for item in items:

        text += f"• {item}\n"



    await update.message.reply_text(text)





# =====================
# ABOUT
# =====================

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):


    await update.message.reply_text(

        "🤖 Smart Search Bot\n\n"

        "Создатель: "
        f"{OWNER}\n\n"

        "Возможности:\n"

        "🌐 Интернет\n"
        "🎵 Музыка\n"
        "🎬 Видео\n"
        "📚 Знания\n"
        "🛒 Покупки\n"
        "🗺 Карты\n\n"

        "Умный поиск работает без ИИ."

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



    add_history(

        user_id,

        text

    )



    categories = smart_search(text)



    if len(categories) > 1:


        await update.message.reply_text(

            result_card(

                text,

                categories

            ),

            reply_markup=multi_menu(

                text,

                categories

            )

        )


        return





    mode = categories[0]



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
# ERROR
# =====================

async def error_handler(
    update,
    context
):

    print(

        "ERROR:",

        repr(context.error)

    )





# =====================
# RUN
# =====================

def run():


    if not BOT_TOKEN:


        raise RuntimeError(

            "BOT_TOKEN не найден"

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




    application.add_handler(

        CommandHandler(

            "start",

            start

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

            "favorite",

            favorite_command

        )

    )



    application.add_handler(

        CommandHandler(

            "about",

            about_command

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



    application.add_error_handler(

        error_handler

    )



    print(

        "✅ SMART SEARCH BOT STARTED"

    )



    application.run_polling()





# =====================
# MAIN
# =====================

if __name__ == "__main__":

    run()
