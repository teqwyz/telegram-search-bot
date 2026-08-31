```python
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

# Ключ DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

PORT = int(os.getenv("PORT", "10000"))

OWNER = "@teqwyz"

app = Flask(__name__)

modes = {}

# Память AI
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
        INSERT INTO history(user_id,text,date)
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
# URL
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
# AI DEEPSEEK
# =========================

def ai_request(text, user_id):

    # Проверяем ключ
    if not DEEPSEEK_API_KEY:

        return (
            "❌ DeepSeek не настроен.\n\n"
            "Добавь переменную DEEPSEEK_API_KEY "
            "в Environment Variables Render."
        )


    # Получаем историю пользователя
    history = ai_memory.get(
        user_id,
        []
    )


    # Добавляем вопрос
    history.append(
        {
            "role": "user",
            "content": text
        }
    )


    # Оставляем последние сообщения
    history = history[-10:]


    try:

        response = requests.post(

            "https://api.deepseek.com/chat/completions",

            headers={

                "Authorization":
                f"Bearer {DEEPSEEK_API_KEY}",

                "Content-Type":
                "application/json"

            },

            json={

                "model":
                "deepseek-chat",

                "messages":

                [
                    {
                        "role":
                        "system",

                        "content":
                        (
                            "Ты умный и дружелюбный "
                            "Telegram помощник. "
                            "Отвечай на русском языке, "
                            "если пользователь пишет по-русски."
                        )
                    }
                ]

                +

                history,

                "temperature":
                0.7

            },

            timeout=60

        )


        # Проверяем HTTP-ошибку
        if response.status_code != 200:

            try:
                data = response.json()
            except Exception:
                data = response.text

            return (
                "❌ DeepSeek вернул ошибку.\n\n"
                f"HTTP: {response.status_code}\n"
                f"{data}"
            )


        data = response.json()


        if "choices" not in data:

            return (
                "❌ В ответе DeepSeek нет результата.\n\n"
                + str(data)
            )


        answer = (
            data["choices"][0]
            ["message"]
            ["content"]
        )


        # Сохраняем ответ AI
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
            "❌ DeepSeek слишком долго отвечает. "
            "Попробуй ещё раз."
        )


    except requests.exceptions.RequestException as e:

        return (
            "❌ Ошибка подключения к DeepSeek:\n"
            + str(e)
        )


    except Exception as e:

        return (
            "❌ Ошибка AI:\n"
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

    save_user(user)

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        SELECT first_seen, requests
        FROM users
        WHERE id=?
        """,
        (user.id,)
    )

    data = cur.fetchone()

    con.close()


    if data:

        await update.message.reply_text(

            f"👤 Профиль\n\n"
            f"ID: {user.id}\n"
            f"Имя: {user.first_name}\n"
            f"Первый запуск: {data[0]}\n"
            f"Запросов: {data[1]}"

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
        SELECT text,date
        FROM history
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (user_id,)
    )

    rows = cur.fetchall()

    con.close()


    if not rows:

        await update.message.reply_text(
            "📜 История пустая."
        )

        return


    result = "📜 Последние запросы:\n\n"


    for item, date in rows:

        result += f"• {item}\n"


    await update.message.reply_text(
        result
    )


# =========================
# ИЗБРАННОЕ
# =========================

async def favorite(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "Используй:\n"
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
        INSERT INTO favorites(user_id,text)
        VALUES(?,?)
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


async def favorites(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        SELECT text
        FROM favorites
        WHERE user_id=?
        """,
        (
            update.effective_user.id,
        )
    )

    rows = cur.fetchall()

    con.close()


    if not rows:

        await update.message.reply_text(
            "⭐ Избранное пустое."
        )

        return


    result = "⭐ Избранное:\n\n"


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
# ОЧИСТКА AI
# =========================

async def clear_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    ai_memory.pop(
        update.effective_user.id,
        None
    )


    await update.message.reply_text(
        "🧠 Память AI очищена."
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
            "Пример:\n"
            "/ask расскажи про космос"
        )

        return


    question = " ".join(
        context.args
    )


    await update.message.reply_text(
        "Печатает..."
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
                url=(
                    "https://open.spotify.com/search/"
                    + q
                )
            )
        ],

        [
            InlineKeyboardButton(
                "🎵 Яндекс Музыка",
                url=(
                    "https://music.yandex.ru/search?text="
                    + q
                )
            )
        ],

        [
            InlineKeyboardButton(
                "🎵 VK Музыка 📱",
                url=(
                    "https://vk.com/audio?"
                    "section=search&q="
                    + q
                )
            )
        ],

        [
            InlineKeyboardButton(
                "🌐 VK Музыка",
                url=(
                    "https://vk.com/audio?"
                    "section=search&q="
                    + q
                )
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
                "▶ YouTube",
                url=(
                    "https://www.youtube.com/results?"
                    "search_query="
                    + q
                )
            )
        ],

        [
            InlineKeyboardButton(
                "▶ VK Видео",
                url=(
                    "https://vk.com/video?"
                    "q="
                    + q
                )
            )
        ],

        [
            InlineKeyboardButton(
                "▶ Rutube",
                url=(
                    "https://rutube.ru/search/?query="
                    + q
                )
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
                "https://ru.wikipedia.org/wiki/"
                + q
            )

        ],


        "shop": [

            (
                "🛒 Яндекс Маркет",
                "https://market.yandex.ru/search?text="
                + q
            ),

            (
                "🛒 Ozon",
                "https://www.ozon.ru/search/?text="
                + q
            ),

            (
                "🛒 Wildberries",
                "https://www.wildberries.ru/catalog/0/"
                "search.aspx?search="
                + q
            )

        ],


        "maps": [

            (
                "🗺 Google Maps",
                "https://www.google.com/maps/search/"
                + q
            ),

            (
                "🗺 Яндекс Карты",
                "https://yandex.ru/maps/?text="
                + q
            ),

            (
                "🗺 2ГИС",
                "https://2gis.ru/search/"
                + q
            ),

            (
                "🗺 Apple Maps",
                "https://maps.apple.com/?q="
                + q
            )

        ]

    }


    buttons = []


    for name, url in links.get(mode, []):

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


# =========================
# ВЕБ ПОИСК
# =========================

def web_search(text):

    q = encode(text)

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🔎 Google",
                url=(
                    "https://www.google.com/search?q="
                    + q
                )
            )
        ],

        [
            InlineKeyboardButton(
                "🔎 Яндекс",
                url=(
                    "https://yandex.ru/search/?text="
                    + q
                )
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
        p in text
        for p in phrases
    )


# =========================
# КНОПКИ
# =========================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return


    await query.answer()


    user_id = query.from_user.id

    modes[user_id] = query.data


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


    await query.edit_message_text(

        "Хорошо, я выбрал этот режим: "
        + names.get(
            query.data,
            "Неизвестно"
        )
        +
        "\n\nОтправь запрос."

    )


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    save_user(user)

    modes[user.id] = "web"


    await update.message.reply_text(

        "Привет, меня зовут durikovich!\n\n"
        "Я поисковый бот с Artificial Intelligence.\n\n"
        "Выбери режим:",

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

        "/start — главное меню\n"
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


    save_user(user)

    add_request(
        user.id,
        text
    )


    # ---------------------
    # СОЗДАТЕЛЬ
    # ---------------------

    if creator_question(text):

        await update.message.reply_text(
            f"Меня создал {OWNER}, только это наш с тобой секрет..."
        )

        return


    # ---------------------
    # ТЕКУЩИЙ РЕЖИМ
    # ---------------------

    mode = modes.get(
        user.id,
        "web"
    )


    # ---------------------
    # AI
    # ---------------------

    if mode == "ai":

        await update.message.reply_text(
            "🤖 Думаю..."
        )


        answer = ai_request(
            text,
            user.id
        )


        await update.message.reply_text(
            answer
        )


        return


    # ---------------------
    # МУЗЫКА
    # ---------------------

    if mode == "music":

        await update.message.reply_text(

            "🎵 Выбери сервис:",

            reply_markup=music_menu(
                text
            )

        )

        return


    # ---------------------
    # ВИДЕО
    # ---------------------

    if mode == "video":

        await update.message.reply_text(

            "🎬 Выбери сервис:",

            reply_markup=video_menu(
                text
            )

        )

        return


    # ---------------------
    # WIKI / SHOP / MAPS
    # ---------------------

    if mode in [

        "wiki",
        "shop",
        "maps"

    ]:

        await update.message.reply_text(

            "Вот что я нашел:",

            reply_markup=other_menu(
                text,
                mode
            )

        )

        return


    # ---------------------
    # WEB
    # ---------------------

    await update.message.reply_text(

        "Гуглю:",

        reply_markup=web_search(
            text
        )

    )


# =========================
# ERROR
# =========================

async def error_handler(
    update,
    context
):

    print(
        "ERROR:",
        context.error
    )


# =========================
# ЗАПУСК
# =========================

def run():

    if not BOT_TOKEN:

        raise RuntimeError(
            "❌ BOT_TOKEN не найден"
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


    # Команды

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


    # Кнопки

    application.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )


    # Обычные сообщения

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message
        )
    )


    application.add_error_handler(
        error_handler
    )


    print("BOT STARTED")


    application.run_polling(
        drop_pending_updates=True
    )


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    run()
```
