import os
import threading
import urllib.parse
import requests

from flask import Flask
from bs4 import BeautifulSoup

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)


# =========================
# FLASK SERVER (RENDER)
# =========================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Telegram Search Bot is running!"



def run_web():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    web_app.run(
        host="0.0.0.0",
        port=port
    )



# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.environ["BOT_TOKEN"]

# УКАЖИ СВОЙ TELEGRAM USERNAME
CREATOR = "@teqwyz"
)



# =========================
# WEB SEARCH
# =========================

def search_web(query):

    url = "https://html.duckduckgo.com/html/"


    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }


    try:

        response = requests.get(
            url,
            params={
                "q": query
            },
            headers=headers,
            timeout=15
        )


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


    except Exception as e:

        print(
            "Search error:",
            e
        )

        return []



    results = []


    for item in soup.select(".result"):


        link = item.select_one(
            ".result__a"
        )


        if not link:
            continue



        results.append(
            {
                "title":
                link.get_text(
                    " ",
                    strip=True
                ),

                "url":
                link.get("href")
            }
        )



    return results




# =========================
# VIDEO SEARCH
# =========================

def video_search(query):

    q = urllib.parse.quote(
        query
    )


    return [

        {
            "title":
            f"🎬 YouTube: {query}",

            "url":
            f"https://youtube.com/results?search_query={q}"
        }

    ]



# =========================
# AUDIO SEARCH
# =========================

def audio_search(query):

    q = urllib.parse.quote(
        query
    )


    return [

        {
            "title":
            f"🎵 Яндекс Музыка: {query}",

            "url":
            f"https://music.yandex.ru/search?text={q}"
        },


        {
            "title":
            f"🎧 VK Музыка: {query}",

            "url":
            f"https://vk.com/audio?q={q}"
        },


        {
            "title":
            f"▶️ YouTube Music: {query}",

            "url":
            f"https://music.youtube.com/search?q={q}"
        }

    ]



# =========================
# DETECT TYPE
# =========================

def detect_type(text):

    text = text.lower()



    video = [
        "видео",
        "ролик",
        "трейлер",
        "клип",
        "фильм"
    ]


    audio = [
        "песня",
        "музыка",
        "трек",
        "альбом",
        "слушать",
        "исполнитель",
        "артист"
    ]



    if any(
        word in text
        for word in video
    ):
        return "video"



    if any(
        word in text
        for word in audio
    ):
        return "audio"



    return "web"




# =========================
# COMMANDS
# =========================

async def start(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):


    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я поисковый бот.\n\n"
        "Могу искать:\n"
        "🔎 сайты\n"
        "🎬 видео\n"
        "🎵 музыку"
    )



async def creator(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):


    await update.message.reply_text(
        f"🤖 Меня создал {CREATOR_USERNAME}"
    )



# =========================
# MESSAGE SEARCH
# =========================

async def search(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):


    query = update.message.text



    msg = await update.message.reply_text(
        "🔎 Ищу..."
    )



    mode = detect_type(
        query
    )



    if mode == "audio":

        results = audio_search(
            query
        )


    elif mode == "video":

        results = video_search(
            query
        )


    else:

        results = search_web(
            query
        )




    if not results:

        await msg.edit_text(
            "😕 Ничего не найдено"
        )

        return




    buttons = []

    text = "🔎 Результаты:\n\n"



    for result in results[:5]:


        text += (
            result["title"]
            +
            "\n\n"
        )


        buttons.append(
            [
                InlineKeyboardButton(
                    "🔗 Открыть",
                    url=result["url"]
                )
            ]
        )




    await msg.edit_text(

        text,

        reply_markup=
        InlineKeyboardMarkup(
            buttons
        )

    )




# =========================
# MAIN
# =========================

def main():

    threading.Thread(
        target=run_web,
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
        MessageHandler(
            filters.Regex(
                "Кто твой создатель"
            ),
            creator
        )
    )



    application.add_handler(
        MessageHandler(
            filters.TEXT
            &
            ~filters.COMMAND,
            search
        )
    )



    print(
        "🤖 Bot started"
    )



    application.run_polling(
        drop_pending_updates=True
    )




if __name__ == "__main__":
    main()
