import os
import threading
import requests

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ContextTypes,
    filters,
)

from database import (
    init_db,
    add_user,
    add_history,
    get_history,
    count_users,
    count_searches,
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

ADMIN_ID = int(
    os.getenv(
        "ADMIN_ID",
        "0"
    )
)


# =====================
# FLASK / RENDER
# =====================

app = Flask(__name__)


@app.route("/")
def home():
    return "🤖 Smart Search Bot 2.3 Online"


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False,
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
            ),
        ],
        [
            InlineKeyboardButton(
                "🎬 Видео",
                callback_data="video"
            ),
            InlineKeyboardButton(
                "📚 Знания",
                callback_data="wiki"
            ),
        ],
        [
            InlineKeyboardButton(
                "🛒 Товары",
                callback_data="shop"
            ),
            InlineKeyboardButton(
                "🗺 Карты",
                callback_data="maps"
            ),
        ],
        [
            InlineKeyboardButton(
                "📰 Новости",
                callback_data="news"
            ),
        ],
        [
            InlineKeyboardButton(
                "⭐ История",
                callback_data="history"
            ),
        ],
        [
            InlineKeyboardButton(
                "ℹ️ О боте",
                callback_data="about"
            ),
        ],
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
    if not update.message:
        return

    user = update.effective_user

    add_user(user)

    modes[user.id] = "web"

    await update.message.reply_text(
        "🤖 Добро пожаловать!\n\n"
        "Я Smart Search Bot 2.3\n\n"
        "Могу искать:\n\n"
        "🌐 сайты\n"
        "🎵 музыку\n"
        "🎬 видео\n"
        "📚 информацию\n"
        "🛒 товары\n"
        "🗺 места\n"
        "📰 новости\n\n"
        "Выбери категорию:",
        reply_markup=main_menu(),
    )


# =====================
# ABOUT
# =====================

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    await update.message.reply_text(
        "🤖 Smart Search Bot 2.3\n\n"
        f"Создатель: {OWNER}\n\n"
        "Возможности:\n\n"
        "✅ SQLite база\n"
        "✅ История поиска\n"
        "✅ Inline Mode\n"
        "✅ Новости\n"
        "✅ Статистика\n"
        "✅ Поиск по категориям\n"
    )


# =====================
# HELP
# =====================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    await update.message.reply_text(
        "📌 Команды бота:\n\n"
        "/start — главное меню\n"
        "/help — помощь\n"
        "/about — информация о боте\n"
        "/history — история поиска\n"
        "/news — режим новостей\n"
        "/admin — статистика администратора\n\n"
        "Также можно использовать Inline Mode:\n"
        "@имя_бота поисковый запрос"
    )


# =====================
# ИСТОРИЯ
# =====================

async def history_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    user_id = update.effective_user.id

    items = get_history(user_id)

    if not items:
        await update.message.reply_text(
            "⭐ История поиска пока пустая."
        )
        return

    text = "⭐ История поиска:\n\n"

    for i, item in enumerate(items, 1):
        text += f"{i}. {item}\n"

    await update.message.reply_text(
        text,
        reply_markup=back_button(),
    )


# =====================
# NEWS
# =====================

async def news_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    user_id = update.effective_user.id

    modes[user_id] = "news"

    await update.message.reply_text(
        "📰 Режим новостей включён.\n\n"
        "✏️ Напиши тему, которую хочешь найти."
    )


def news_menu(text):
    q = encode(text)

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📰 Google News",
                url=f"https://news.google.com/search?q={q}"
            )
        ],
        [
            InlineKeyboardButton(
                "📰 Яндекс Новости",
                url=f"https://yandex.ru/news/search?text={q}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔎 Bing News",
                url=f"https://www.bing.com/news/search?q={q}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅ Главное меню",
                callback_data="menu"
            )
        ],
    ])


# =====================
# ПОИСКОВЫЕ МЕНЮ
# =====================

def web_menu(text):
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
                "🔎 DuckDuckGo",
                url=f"https://duckduckgo.com/?q={q}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅ Главное меню",
                callback_data="menu"
            )
        ],
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
                "🎵 SoundCloud",
                url=f"https://soundcloud.com/search?q={q}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅ Главное меню",
                callback_data="menu"
            )
        ],
    ])


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
        [
            InlineKeyboardButton(
                "▶ Dailymotion",
                url=f"https://www.dailymotion.com/search/{q}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅ Главное меню",
                callback_data="menu"
            )
        ],
    ])


def other_menu(text, mode):
    q = encode(text)

    links = {
        "wiki": [
            (
                "📚 Википедия",
                f"https://ru.wikipedia.org/wiki/{q}"
            ),
            (
                "🔎 Google",
                f"https://www.google.com/search?q={q}"
            ),
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
            ),
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
        ],
    }

    buttons = []

    for name, url in links.get(mode, []):
        buttons.append([
            InlineKeyboardButton(
                name,
                url=url
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "⬅ Главное меню",
            callback_data="menu"
        )
    ])

    return InlineKeyboardMarkup(buttons)


# =====================
# CALLBACK BUTTONS
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
            "🤖 Главное меню\n\n"
            "Выбери способ поиска:",
            reply_markup=main_menu(),
        )

        return

    # История
    if data == "history":
        items = get_history(user_id)

        if not items:
            await query.edit_message_text(
                "⭐ История поиска пустая.",
                reply_markup=back_button(),
            )
            return

        text = "⭐ История поиска:\n\n"

        for i, item in enumerate(items, 1):
            text += f"{i}. {item}\n"

        await query.edit_message_text(
            text,
            reply_markup=back_button(),
        )

        return

    # О боте
    if data == "about":
        await query.edit_message_text(
            "🤖 Smart Search Bot 2.3\n\n"
            f"Создатель: {OWNER}\n\n"
            "Функции:\n"
            "✅ SQLite\n"
            "✅ История\n"
            "✅ Inline Mode\n"
            "✅ Новости\n"
            "✅ Статистика",
            reply_markup=back_button(),
        )

        return

    names = {
        "web": "🌐 Интернет",
        "music": "🎵 Музыка",
        "video": "🎬 Видео",
        "wiki": "📚 Знания",
        "shop": "🛒 Товары",
        "maps": "🗺 Карты",
        "news": "📰 Новости",
    }

    if data not in names:
        return

    modes[user_id] = data

    await query.edit_message_text(
        "✅ Выбран режим:\n\n"
        f"{names[data]}\n\n"
        "✏️ Напиши запрос.",
        reply_markup=main_menu(),
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

    user = update.effective_user
    user_id = user.id

    add_user(user)
    add_history(user_id, text)

    mode = modes.get(
        user_id,
        "web"
    )

    # Новости
    if mode == "news":
        await update.message.reply_text(
            "📰 Новости:",
            reply_markup=news_menu(text),
        )
        return

    # Интернет
    if mode == "web":
        await update.message.reply_text(
            "🌐 Поиск:",
            reply_markup=web_menu(text),
        )
        return

    # Музыка
    if mode == "music":
        await update.message.reply_text(
            "🎵 Музыка:",
            reply_markup=music_menu(text),
        )
        return

    # Видео
    if mode == "video":
        await update.message.reply_text(
            "🎬 Видео:",
            reply_markup=video_menu(text),
        )
        return

    # Wiki / Shop / Maps
    await update.message.reply_text(
        "🔎 Результаты:",
        reply_markup=other_menu(
            text,
            mode
        ),
    )


# =====================
# INLINE MODE
# =====================

async def inline_search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.inline_query.query.strip()

    if not query:
        return

    q = encode(query)

    results = [
        InlineQueryResultArticle(
            id="google",
            title="🔎 Google",
            description=f"Поиск: {query}",
            input_message_content=InputTextMessageContent(
                f"https://www.google.com/search?q={q}"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔎 Открыть Google",
                        url=f"https://www.google.com/search?q={q}"
                    )
                ]
            ]),
        ),

        InlineQueryResultArticle(
            id="yandex",
            title="🔎 Яндекс",
            description=f"Поиск: {query}",
            input_message_content=InputTextMessageContent(
                f"https://yandex.ru/search/?text={q}"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔎 Открыть Яндекс",
                        url=f"https://yandex.ru/search/?text={q}"
                    )
                ]
            ]),
        ),

        InlineQueryResultArticle(
            id="bing",
            title="🔎 Bing",
            description=f"Поиск: {query}",
            input_message_content=InputTextMessageContent(
                f"https://www.bing.com/search?q={q}"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔎 Открыть Bing",
                        url=f"https://www.bing.com/search?q={q}"
                    )
                ]
            ]),
        ),

        InlineQueryResultArticle(
            id="news",
            title="📰 Новости",
            description=f"Новости по теме: {query}",
            input_message_content=InputTextMessageContent(
                f"https://news.google.com/search?q={q}"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📰 Открыть новости",
                        url=f"https://news.google.com/search?q={q}"
                    )
                ]
            ]),
        ),
    ]

    await update.inline_query.answer(
        results,
        cache_time=1,
        is_personal=True,
    )


# =====================
# ADMIN
# =====================

async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Нет доступа."
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
            "BOT_TOKEN отсутствует в Environment Variables"
        )

    # SQLite
    init_db()

    # Flask / Render
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    # Telegram
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
    # CALLBACK
    # =====================

    application.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    # =====================
    # INLINE
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
            filters.TEXT & ~filters.COMMAND,
            message
        )
    )

    # =====================
    # ERROR
    # =====================

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
