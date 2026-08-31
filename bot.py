import os
import threading
import sqlite3
import requests

from datetime import datetime

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


# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

PORT = int(
    os.getenv(
        "PORT",
        "10000"
    )
)

OWNER = "@teqwyz"


app = Flask(__name__)


modes = {}

ai_memory = {}


# =========================
# SQLITE
# =========================

DB = "bot.db"


def db():

    return sqlite3.connect(DB)



def init_db():

    con = db()

    cur = con.cursor()


    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY,

        username TEXT,

        first_seen TEXT,

        requests INTEGER DEFAULT 0

    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        text TEXT,

        date TEXT

    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorites(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        text TEXT

    )
    """)


    con.commit()

    con.close()



def save_user(user):

    con = db()

    cur = con.cursor()


    cur.execute(
        "SELECT id FROM users WHERE id=?",
        (user.id,)
    )


    if not cur.fetchone():

        cur.execute(
            """
            INSERT INTO users
            VALUES(?,?,?,?)
            """,
            (
                user.id,
                user.username or "",
                datetime.now().isoformat(),
                0
            )
        )


    con.commit()

    con.close()



def add_request(user_id, text):

    con = db()

    cur = con.cursor()


    cur.execute(
        """
        UPDATE users
        SET requests=requests+1
        WHERE id=?
        """,
        (user_id,)
    )


    cur.execute(
        """
        INSERT INTO history
        (
            user_id,
            text,
            date
        )

        VALUES(?,?,?)

        """,
        (
            user_id,
            text,
            datetime.now().isoformat()
        )
    )


    con.commit()

    con.close()



# =========================
# FLASK / RENDER
# =========================


@app.route("/")
def home():

    return "Telegram AI Search Bot is running!"



def run_flask():

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )



# =========================
# UTILS
# =========================


def encode(text):

    return requests.utils.quote(
        text,
        safe=""
    )



# =========================
# ГЛАВНОЕ МЕНЮ
# =========================


def main_menu():

    return InlineKeyboardMarkup([


        [
            InlineKeyboardButton(
                "🌐 Веб",
                callback_data="web"
            )
        ],


        [
            InlineKeyboardButton(
                "🤖 AI",
                callback_data="ai"
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

# =========================
# OPENAI AI
# =========================

def ai_request(text, user_id):

    if not OPENAI_API_KEY:

        return (
            "❌ OPENAI_API_KEY не настроен.\n\n"
            "Добавь OPENAI_API_KEY в Environment Variables "
            "на Render."
        )


    history = ai_memory.get(
        user_id,
        []
    )


    history.append(
        {
            "role": "user",
            "content": text
        }
    )


    # Храним последние 10 сообщений
    history = history[-10:]


    messages = [

        {
            "role": "system",
            "content": (
                "Ты умный и дружелюбный Telegram-помощник. "
                "Отвечай на русском языке, если пользователь "
                "не попросил другой язык. "
                "Отвечай понятно и по существу."
            )
        }

    ] + history


    try:

        response = requests.post(

            "https://api.openai.com/v1/chat/completions",

            headers={
                "Authorization":
                    f"Bearer {OPENAI_API_KEY}",

                "Content-Type":
                    "application/json"
            },

            json={

                "model":
                    "gpt-4.1-mini",

                "messages":
                    messages,

                "temperature":
                    0.7,

                "max_tokens":
                    1500

            },

            timeout=60

        )


        # Проверяем HTTP-ошибку
        if response.status_code != 200:

            try:

                error_data = response.json()

            except Exception:

                error_data = response.text


            print(
                "OPENAI ERROR:",
                error_data
            )


            return (
                "❌ Ошибка OpenAI:\n\n"
                + str(error_data)
            )


        data = response.json()


        if "choices" not in data:

            print(
                "OPENAI INVALID RESPONSE:",
                data
            )


            return (
                "❌ OpenAI вернул неожиданный ответ:\n"
                + str(data)
            )


        answer = (
            data["choices"][0]
            ["message"]
            ["content"]
        )


        if not answer:

            return (
                "❌ OpenAI не вернул текст ответа."
            )


        history.append(

            {
                "role":
                    "assistant",

                "content":
                    answer
            }

        )


        ai_memory[user_id] = history[-10:]


        return answer


    except requests.exceptions.Timeout:

        return (
            "❌ OpenAI слишком долго отвечает.\n"
            "Попробуй ещё раз."
        )


    except requests.exceptions.ConnectionError:

        return (
            "❌ Не удалось подключиться к OpenAI.\n"
            "Проверь интернет-соединение Render."
        )


    except Exception as e:

        print(
            "OPENAI EXCEPTION:",
            repr(e)
        )


        return (
            "❌ Ошибка соединения с OpenAI:\n"
            + str(e)
        )


# =========================
# ПРОФИЛЬ
# =========================

async def profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if not user:

        return


    save_user(user)


    con = db()

    cur = con.cursor()


    cur.execute(

        """
        SELECT first_seen, requests
        FROM users
        WHERE id=?
        """,

        (
            user.id,
        )

    )


    data = cur.fetchone()


    con.close()


    if not data:

        await update.message.reply_text(
            "❌ Профиль не найден."
        )

        return


    await update.message.reply_text(

        f"👤 Профиль\n\n"

        f"🆔 ID: {user.id}\n"

        f"👤 Имя: {user.first_name}\n"

        f"🔗 Username: "
        f"@{user.username if user.username else 'нет'}\n\n"

        f"📅 Первый запуск:\n"
        f"{data[0]}\n\n"

        f"📊 Запросов: {data[1]}"

    )


# =========================
# ИСТОРИЯ
# =========================

async def history_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id


    con = db()

    cur = con.cursor()


    cur.execute(

        """
        SELECT text, date
        FROM history
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """,

        (
            user_id,
        )

    )


    rows = cur.fetchall()


    con.close()


    if not rows:

        await update.message.reply_text(

            "📜 История пустая."

        )

        return


    result = (
        "📜 Последние 10 запросов:\n\n"
    )


    for item, date in rows:

        result += (
            f"• {item}\n"
        )


    await update.message.reply_text(
        result
    )


# =========================
# ДОБАВИТЬ В ИЗБРАННОЕ
# =========================

async def favorite(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(

            "⭐ Использование:\n\n"
            "/favorite текст"

        )

        return


    text = " ".join(
        context.args
    )


    con = db()

    cur = con.cursor()


    cur.execute(

        """
        INSERT INTO favorites
        (
            user_id,
            text
        )
        VALUES(?, ?)
        """,

        (
            update.effective_user.id,
            text
        )

    )


    con.commit()

    con.close()


    await update.message.reply_text(

        "⭐ Добавлено в избранное."

    )


# =========================
# ИЗБРАННОЕ
# =========================

async def favorites(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id


    con = db()

    cur = con.cursor()


    cur.execute(

        """
        SELECT text
        FROM favorites
        WHERE user_id=?
        ORDER BY id DESC
        """,

        (
            user_id,
        )

    )


    rows = cur.fetchall()


    con.close()


    if not rows:

        await update.message.reply_text(

            "⭐ Избранное пустое."

        )

        return


    result = (
        "⭐ Избранное:\n\n"
    )


    for row in rows:

        result += (
            "• "
            + row[0]
            + "\n"
        )


    await update.message.reply_text(
        result
    )


# =========================
# ОЧИСТКА ПАМЯТИ AI
# =========================

async def clear_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id


    ai_memory.pop(
        user_id,
        None
    )


    await update.message.reply_text(

        "🧠 Память AI очищена.\n\n"
        "Следующий вопрос начнёт новый диалог."

    )


# =========================
# /ASK
# =========================

async def ask(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(

            "🤖 Использование:\n\n"
            "/ask твой вопрос\n\n"
            "Например:\n"
            "/ask расскажи про космос"

        )

        return


    question = " ".join(
        context.args
    )


    await update.message.chat.send_action(
        "typing"
    )


    answer = ai_request(

        question,

        update.effective_user.id

    )


    await update.message.reply_text(
        answer
    )

# =========================
# МУЗЫКА
# =========================

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
                "🎵 VK Музыка 📱",
                url=f"vk://vk.com/audio?section=search&q={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "🌐 VK Музыка — браузер",
                url=f"https://vk.com/audio?section=search&q={q}"
            )
        ]

    ])


# =========================
# ВИДЕО
# =========================

def video_menu(text):

    q = encode(text)

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "▶️ YouTube",
                url=(
                    "https://www.youtube.com/results"
                    f"?search_query={q}"
                )
            )
        ],

        [
            InlineKeyboardButton(
                "▶️ VK Видео",
                url=f"https://vk.com/video?q={q}"
            )
        ],

        [
            InlineKeyboardButton(
                "▶️ Rutube",
                url=f"https://rutube.ru/search/?query={q}"
            )
        ]

    ])


# =========================
# WIKI / SHOP / MAPS
# =========================

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
                (
                    "https://www.wildberries.ru/catalog/0/"
                    f"search.aspx?search={q}"
                )
            )

        ],

        "maps": [

            (
                "🗺 Google Maps",
                f"https://www.google.com/maps/search/{q}"
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

    buttons_list = []


    for name, url in links.get(mode, []):

        buttons_list.append(

            [
                InlineKeyboardButton(
                    name,
                    url=url
                )
            ]

        )


    return InlineKeyboardMarkup(
        buttons_list
    )


# =========================
# WEB SEARCH
# =========================

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
        ]

    ])


# =========================
# СОЗДАТЕЛЬ
# =========================

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
        phrase in text
        for phrase in phrases
    )


# =========================
# КНОПКИ МЕНЮ
# =========================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    if query is None:
        return


    # Подтверждаем нажатие кнопки
    await query.answer()


    user_id = query.from_user.id

    mode = query.data


    # Сохраняем выбранный режим
    modes[user_id] = mode


    names = {

        "web":
            "🌐 Веб",

        "ai":
            "🤖 AI",

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


    selected_name = names.get(
        mode,
        "Неизвестно"
    )


    try:

        await query.edit_message_text(

            text=(
                f"✅ Режим выбран: {selected_name}\n\n"
                "Отправь запрос."
            ),

            reply_markup=main_menu()

        )


    except Exception as e:

        print(
            "BUTTON ERROR:",
            repr(e)
        )


        # Если сообщение уже нельзя изменить,
        # отправляем новое
        try:

            await query.message.reply_text(

                text=(
                    f"✅ Режим выбран: {selected_name}\n\n"
                    "Отправь запрос."
                ),

                reply_markup=main_menu()

            )

        except Exception as inner_error:

            print(
                "BUTTON SEND ERROR:",
                repr(inner_error)
            )


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if not user:
        return


    save_user(user)


    modes[user.id] = "web"


    await update.message.reply_text(

        "🤖 Привет! Я durikovich.\n\n"
        "Я поисковый бот с AI.\n"
        "Выбирай режим:",

        reply_markup=main_menu()

    )


# =========================
# HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "📌 Команды:\n\n"

        "/start — открыть меню\n"
        "/help — помощь\n"
        "/ask текст — спросить AI\n"
        "/profile — профиль\n"
        "/history — история запросов\n"
        "/favorite текст — добавить в избранное\n"
        "/favorites — показать избранное\n"
        "/clear — очистить память AI"

    )


# =========================
# СООБЩЕНИЯ
# =========================

async def message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    if not update.message.text:
        return


    text = update.message.text.strip()


    if not text:
        return


    user = update.effective_user


    if not user:
        return


    save_user(user)


    add_request(
        user.id,
        text
    )


    # =====================
    # СОЗДАТЕЛЬ
    # =====================

    if creator_question(text):

        await update.message.reply_text(

            f"🤖 Меня создал {OWNER}"

        )

        return


    # =====================
    # ТЕКУЩИЙ РЕЖИМ
    # =====================

    mode = modes.get(
        user.id,
        "web"
    )


    # =====================
    # AI
    # =====================

    if mode == "ai":

        await update.message.chat.send_action(
            "typing"
        )


        answer = ai_request(

            text,

            user.id

        )


        await update.message.reply_text(
            answer
        )

        return


    # =====================
    # МУЗЫКА
    # =====================

    if mode == "music":

        await update.message.reply_text(

            "🎵 Выбери сервис:",

            reply_markup=music_menu(
                text
            )

        )

        return


    # =====================
    # ВИДЕО
    # =====================

    if mode == "video":

        await update.message.reply_text(

            "🎬 Выбери сервис:",

            reply_markup=video_menu(
                text
            )

        )

        return


    # =====================
    # WIKI / SHOP / MAPS
    # =====================

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


    # =====================
    # WEB
    # =====================

    await update.message.reply_text(

        "🌐 Поиск:",

        reply_markup=web_search(
            text
        )

    )

# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "BOT ERROR:",
        repr(context.error)
    )


# =========================
# ЗАПУСК
# =========================

def run():

    # Проверяем токен Telegram
    if not BOT_TOKEN:

        raise RuntimeError(
            "❌ BOT_TOKEN не найден в Environment Variables"
        )


    # Проверяем OpenAI
    if not OPENAI_API_KEY:

        print(
            "⚠️ OPENAI_API_KEY не найден."
            " AI работать не будет."
        )


    # Создаём таблицы SQLite
    init_db()


    # =========================
    # FLASK ДЛЯ RENDER
    # =========================

    flask_thread = threading.Thread(

        target=run_flask,

        daemon=True

    )

    flask_thread.start()


    # =========================
    # TELEGRAM APPLICATION
    # =========================

    application = (

        Application

        .builder()

        .token(BOT_TOKEN)

        .build()

    )


    # =========================
    # КОМАНДЫ
    # =========================

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
            "ask",
            ask
        )

    )


    application.add_handler(

        CommandHandler(
            "profile",
            profile
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
            favorite
        )

    )


    application.add_handler(

        CommandHandler(
            "favorites",
            favorites
        )

    )


    application.add_handler(

        CommandHandler(
            "clear",
            clear_ai
        )

    )


    # =========================
    # INLINE-КНОПКИ
    # =========================

    application.add_handler(

        CallbackQueryHandler(
            buttons
        )

    )


    # =========================
    # ОБЫЧНЫЕ СООБЩЕНИЯ
    # =========================

    application.add_handler(

        MessageHandler(

            filters.TEXT
            & ~filters.COMMAND,

            message

        )

    )


    # =========================
    # ОШИБКИ
    # =========================

    application.add_error_handler(

        error_handler

    )


    print(
        "=============================="
    )

    print(
        "🤖 BOT STARTED"
    )

    print(
        "🌐 Flask server started"
    )

    print(
        "🔘 Inline buttons enabled"
    )

    print(
        "🧠 OpenAI enabled:",
        bool(OPENAI_API_KEY)
    )

    print(
        "=============================="
    )


    # =========================
    # ЗАПУСК TELEGRAM
    # =========================

    application.run_polling(

        drop_pending_updates=True

    )


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    run()
