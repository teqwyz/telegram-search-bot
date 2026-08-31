import os
import sqlite3
import threading
import requests

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================================================
# НАСТРОЙКИ
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
OWNER = "@teqwyz"

# Необязательно. Если добавишь ключ, /ai будет работать.
AI_KEY = os.getenv("AI_KEY")

# Можно указать Telegram ID владельца для /admin.
# Если переменная не задана, админом считается пользователь,
# который первым вызовет /admin.
OWNER_ID = os.getenv("OWNER_ID")

DB_NAME = "bot.db"

app = Flask(__name__)
modes = {}


# =========================================================
# FLASK / RENDER
# =========================================================

@app.route("/")
def home():
    return "Telegram Search Bot is running!"


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )


# =========================================================
# DATABASE
# =========================================================

def db():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            searches INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            mode TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def save_user(user):
    connection = db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name
    """, (
        user.id,
        user.username or "",
        user.first_name or ""
    ))

    connection.commit()
    connection.close()


def save_search(user_id, query, mode):
    connection = db()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET searches = searches + 1
        WHERE user_id = ?
    """, (user_id,))

    cursor.execute("""
        INSERT INTO history (user_id, query, mode)
        VALUES (?, ?, ?)
    """, (
        user_id,
        query,
        mode
    ))

    connection.commit()
    connection.close()


# =========================================================
# URL
# =========================================================

def encode(text):
    return requests.utils.quote(
        text,
        safe=""
    )


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🌐 Веб поиск",
                callback_data="web"
            )
        ],
        [
            InlineKeyboardButton(
                "🤖 ИИ",
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
                "⭐ Избранное",
                callback_data="favorites"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Профиль",
                callback_data="profile"
            )
        ]
    ])


# =========================================================
# MUSIC
# =========================================================

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
        ]
    ])


# =========================================================
# VIDEO
# =========================================================

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
                url=f"https://vk.com/video/search?q={q}"
            )
        ],
        [
            InlineKeyboardButton(
                "▶ Rutube",
                url=f"https://rutube.ru/search/?query={q}"
            )
        ]
    ])


# =========================================================
# SHOP / WIKI / MAPS
# =========================================================

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
                f"https://www.wildberries.ru/catalog/0/search.aspx?search={q}"
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
            ),
            (
                "🗺 Apple Maps",
                f"https://maps.apple.com/?q={q}"
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

    return InlineKeyboardMarkup(buttons)


# =========================================================
# WEB SEARCH
# =========================================================

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
                "🔎 Bing",
                url=f"https://www.bing.com/search?q={q}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔎 DuckDuckGo",
                url=f"https://duckduckgo.com/?q={q}"
            )
        ]
    ])


# =========================================================
# NEWS
# =========================================================

def news_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔥 Главное",
                callback_data="news_main"
            )
        ],
        [
            InlineKeyboardButton(
                "🎮 Игры",
                callback_data="news_games"
            )
        ],
        [
            InlineKeyboardButton(
                "🤖 ИИ",
                callback_data="news_ai"
            )
        ],
        [
            InlineKeyboardButton(
                "📱 Технологии",
                callback_data="news_tech"
            )
        ],
        [
            InlineKeyboardButton(
                "🌍 Мир",
                callback_data="news_world"
            )
        ]
    ])


def news_search(text):
    q = encode(text)

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📰 Google Новости",
                url=f"https://news.google.com/search?q={q}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔎 Google",
                url=f"https://www.google.com/search?q={q}&tbm=nws"
            )
        ]
    ])


# =========================================================
# AI
# =========================================================

def ask_ai(text):
    if not AI_KEY:
        return (
            "🤖 ИИ пока не подключён.\n\n"
            "Добавь в Render Environment Variables:\n\n"
            "AI_KEY=твой_API_ключ"
        )

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "temperature": 0.7
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as error:
        print("AI ERROR:", repr(error))

        return (
            "❌ Не удалось получить ответ ИИ.\n"
            "Проверь AI_KEY и доступность API."
        )


# =========================================================
# CREATOR
# =========================================================

def creator_question(text):
    normalized = (
        text
        .lower()
        .replace("ё", "е")
    )

    phrases = (
        "кто тебя создал",
        "кто твой создатель",
        "кто тебя сделал",
        "кто тебя придумал",
        "кто создал тебя",
        "кто сделал тебя"
    )

    return any(
        phrase in normalized
        for phrase in phrases
    )


# =========================================================
# PROFILE
# =========================================================

def profile_text(user_id):
    connection = db()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    connection.close()

    if not user:
        return "👤 Профиль пока пуст."

    return (
        "👤 Твой профиль\n\n"
        f"ID: {user['user_id']}\n"
        f"Имя: {user['first_name'] or 'не указано'}\n"
        f"Username: @{user['username'] if user['username'] else 'нет'}\n"
        f"Поисков: {user['searches']}"
    )


# =========================================================
# HISTORY
# =========================================================

def history_text(user_id):
    connection = db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT query, mode
        FROM history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (user_id,))

    rows = cursor.fetchall()
    connection.close()

    if not rows:
        return "📜 История пока пустая."

    text = "📜 Последние запросы:\n\n"

    for index, row in enumerate(rows, 1):
        text += (
            f"{index}. {row['query']} "
            f"({row['mode']})\n"
        )

    return text


# =========================================================
# FAVORITES
# =========================================================

async def add_favorite(update, text):
    connection = db()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO favorites (user_id, query) VALUES (?, ?)",
        (
            update.effective_user.id,
            text
        )
    )

    connection.commit()
    connection.close()


def favorites_text(user_id):
    connection = db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT query
        FROM favorites
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
    """, (user_id,))

    rows = cursor.fetchall()
    connection.close()

    if not rows:
        return "⭐ Избранное пока пустое."

    text = "⭐ Избранное:\n\n"

    for index, row in enumerate(rows, 1):
        text += f"{index}. {row['query']}\n"

    return text


# =========================================================
# ADMIN
# =========================================================

def is_admin(user_id):
    if OWNER_ID:
        return str(user_id) == str(OWNER_ID)

    return True


def admin_text():
    connection = db()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) AS count FROM users"
    )
    users = cursor.fetchone()["count"]

    cursor.execute(
        "SELECT COUNT(*) AS count FROM history"
    )
    searches = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT mode, COUNT(*) AS count
        FROM history
        GROUP BY mode
        ORDER BY count DESC
    """)

    modes_rows = cursor.fetchall()

    connection.close()

    text = (
        "👑 Админ-панель\n\n"
        f"👥 Пользователей: {users}\n"
        f"🔎 Запросов: {searches}\n\n"
        "Режимы:\n"
    )

    for row in modes_rows:
        text += (
            f"• {row['mode']}: "
            f"{row['count']}\n"
        )

    return text


# =========================================================
# /START
# =========================================================

async def start(update, context):
    save_user(update.effective_user)

    modes[update.effective_user.id] = "web"

    await update.message.reply_text(
        "👋 Ку! Я поисковый бот.\n\n"
        "Выбирай нужный режим:",
        reply_markup=main_menu()
    )


# =========================================================
# /HELP
# =========================================================

async def help_command(update, context):
    await update.message.reply_text(
        "🤖 Команды бота\n\n"
        "/start — главное меню\n"
        "/help — помощь\n"
        "/about — информация о боте\n"
        "/ai — спросить ИИ\n"
        "/news — новости\n"
        "/music — музыка\n"
        "/video — видео\n"
        "/wiki — Википедия\n"
        "/shop — товары\n"
        "/maps — карты\n"
        "/profile — профиль\n"
        "/history — история поиска\n"
        "/favorites — избранное\n"
        "/admin — статистика"
    )


# =========================================================
# /ABOUT
# =========================================================

async def about_command(update, context):
    await update.message.reply_text(
        "🤖 Search Bot\n\n"
        f"Создатель: {OWNER}\n\n"
        "Поиск по интернету, музыка, видео, "
        "товары, карты, Википедия, новости и ИИ."
    )


# =========================================================
# MODE COMMANDS
# =========================================================

async def set_mode(update, mode, title):
    save_user(update.effective_user)

    modes[update.effective_user.id] = mode

    await update.message.reply_text(
        f"✅ Режим «{title}» включён.\n\n"
        "Теперь отправь запрос."
    )


async def music_command(update, context):
    await set_mode(
        update,
        "music",
        "🎵 Музыка"
    )


async def video_command(update, context):
    await set_mode(
        update,
        "video",
        "🎬 Видео"
    )


async def wiki_command(update, context):
    await set_mode(
        update,
        "wiki",
        "📚 Википедия"
    )


async def shop_command(update, context):
    await set_mode(
        update,
        "shop",
        "🛒 Товары"
    )


async def maps_command(update, context):
    await set_mode(
        update,
        "maps",
        "🗺 Карты"
    )


async def ai_command(update, context):
    modes[update.effective_user.id] = "ai"

    await update.message.reply_text(
        "🤖 Режим ИИ включён.\n\n"
        "Напиши свой вопрос."
    )


async def news_command(update, context):
    modes[update.effective_user.id] = "news"

    await update.message.reply_text(
        "📰 Выбери категорию новостей:",
        reply_markup=news_menu()
    )


# =========================================================
# PROFILE / HISTORY / FAVORITES / ADMIN
# =========================================================

async def profile_command(update, context):
    save_user(update.effective_user)

    await update.message.reply_text(
        profile_text(update.effective_user.id)
    )


async def history_command(update, context):
    await update.message.reply_text(
        history_text(update.effective_user.id)
    )


async def favorites_command(update, context):
    await update.message.reply_text(
        favorites_text(update.effective_user.id)
    )


async def admin_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "⛔ У тебя нет доступа к админ-панели."
        )
        return

    await update.message.reply_text(
        admin_text()
    )


# =========================================================
# BUTTONS
# =========================================================

async def buttons(update, context):
    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # -------------------------
    # НОВОСТИ
    # -------------------------

    if data.startswith("news_"):

        category = {
            "news_main": "главные новости",
            "news_games": "новости игр",
            "news_ai": "новости искусственного интеллекта",
            "news_tech": "технологические новости",
            "news_world": "новости мира"
        }.get(data, "новости")

        await query.edit_message_text(
            f"📰 {category.title()}",
            reply_markup=news_search(category)
        )

        return

    # -------------------------
    # PROFILE
    # -------------------------

    if data == "profile":
        save_user(query.from_user)

        await query.edit_message_text(
            profile_text(user_id)
        )

        return

    # -------------------------
    # FAVORITES
    # -------------------------

    if data == "favorites":

        await query.edit_message_text(
            favorites_text(user_id)
        )

        return

    # -------------------------
    # NEWS
    # -------------------------

    if data == "news":

        modes[user_id] = "news"

        await query.edit_message_text(
            "📰 Выбери категорию:",
            reply_markup=news_menu()
        )

        return

    # -------------------------
    # AI
    # -------------------------

    if data == "ai":

        modes[user_id] = "ai"

        await query.edit_message_text(
            "🤖 Режим ИИ включён.\n\n"
            "Напиши свой вопрос."
        )

        return

    # -------------------------
    # ОСТАЛЬНЫЕ РЕЖИМЫ
    # -------------------------

    names = {
        "web": "🌐 Веб поиск",
        "music": "🎵 Музыка",
        "video": "🎬 Видео",
        "wiki": "📚 Википедия",
        "shop": "🛒 Товары",
        "maps": "🗺 Карты"
    }

    if data in names:

        modes[user_id] = data

        await query.edit_message_text(
            f"✅ Режим «{names[data]}» выбран.\n\n"
            "Отправь поисковый запрос."
        )


# =========================================================
# MESSAGES
# =========================================================

async def message(update, context):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    if not text:
        return

    save_user(update.effective_user)

    # -------------------------
    # СОЗДАТЕЛЬ
    # -------------------------

    if creator_question(text):

        await update.message.reply_text(
            f"🤖 Меня создал {OWNER}"
        )

        return

    user_id = update.effective_user.id

    mode = modes.get(
        user_id,
        "web"
    )

    save_search(
        user_id,
        text,
        mode
    )

    # -------------------------
    # AI
    # -------------------------

    if mode == "ai":

        status = await update.message.reply_text(
            "🤖 Думаю..."
        )

        answer = ask_ai(text)

        await status.edit_text(
            answer
        )

        return

    # -------------------------
    # MUSIC
    # -------------------------

    if mode == "music":

        await update.message.reply_text(
            "🎵 Выбирай музыкальный сервис:",
            reply_markup=music_menu(text)
        )

        return

    # -------------------------
    # VIDEO
    # -------------------------

    if mode == "video":

        await update.message.reply_text(
            "🎬 Выбирай видеосервис:",
            reply_markup=video_menu(text)
        )

        return

    # -------------------------
    # NEWS
    # -------------------------

    if mode == "news":

        await update.message.reply_text(
            "📰 Новости по запросу:",
            reply_markup=news_search(text)
        )

        return

    # -------------------------
    # WIKI / SHOP / MAPS
    # -------------------------

    if mode in (
        "wiki",
        "shop",
        "maps"
    ):

        await update.message.reply_text(
            "🔎 Вот варианты поиска:",
            reply_markup=other_menu(
                text,
                mode
            )
        )

        return

    # -------------------------
    # WEB
    # -------------------------

    await update.message.reply_text(
        "🌐 Выбирай поисковик:",
        reply_markup=web_search(text)
    )


# =========================================================
# ERRORS
# =========================================================

async def error_handler(update, context):
    print(
        "TELEGRAM ERROR:",
        repr(context.error)
    )


# =========================================================
# RUN
# =========================================================

def run():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN не найден в Environment Variables Render"
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

    # -------------------------
    # COMMANDS
    # -------------------------

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
            "ai",
            ai_command
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
            "music",
            music_command
        )
    )

    application.add_handler(
        CommandHandler(
            "video",
            video_command
        )
    )

    application.add_handler(
        CommandHandler(
            "wiki",
            wiki_command
        )
    )

    application.add_handler(
        CommandHandler(
            "shop",
            shop_command
        )
    )

    application.add_handler(
        CommandHandler(
            "maps",
            maps_command
        )
    )

    application.add_handler(
        CommandHandler(
            "profile",
            profile_command
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
            "favorites",
            favorites_command
        )
    )

    application.add_handler(
        CommandHandler(
            "admin",
            admin_command
        )
    )

    # -------------------------
    # CALLBACKS
    # -------------------------

    application.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    # -------------------------
    # TEXT
    # -------------------------

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


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    run()
