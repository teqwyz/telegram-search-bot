import os
import threading
import requests
import urllib.parse
import html

from bs4 import BeautifulSoup
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
    ContextTypes,
    filters
)


# =====================
# CONFIG
# =====================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN не найден")


# =====================
# FLASK
# =====================

app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram Search Bot OK"



def run_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )



# =====================
# DUCKDUCKGO SEARCH
# =====================


def fix_url(url):

    """
    Превращает ссылку DuckDuckGo
    в настоящую ссылку сайта
    """

    try:

        parsed = urllib.parse.urlparse(url)

        query = urllib.parse.parse_qs(
            parsed.query
        )


        if "uddg" in query:

            return urllib.parse.unquote(
                query["uddg"][0]
            )


    except Exception:
        pass


    return url



def search_duckduckgo(query):

    url = (
        "https://html.duckduckgo.com/html/"
    )


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
            timeout=20
        )


        response.raise_for_status()


    except Exception as e:

        print(
            "Ошибка поиска:",
            e
        )

        return []



    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    results = []


    for item in soup.select(
        ".result"
    )[:5]:


        link = item.select_one(
            ".result__a"
        )


        if not link:
            continue


        title = link.get_text(
            " ",
            strip=True
        )


        url = fix_url(
            link.get("href")
        )


        desc = item.select_one(
            ".result__snippet"
        )


        description = ""


        if desc:

            description = desc.get_text(
                " ",
                strip=True
            )


        results.append({

            "title": title,

            "url": url,

            "description": description

        })


    print(
        "Найдено:",
        len(results)
    )


    return results



# =====================
# TELEGRAM
# =====================


async def start(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "👋 Привет!\n\n"
        "Я бот поиска.\n\n"
        "Напиши запрос:"
        "\n\n🔎 GTA 6"
        "\n🔎 Новости ИИ"
        "\n🔎 Павел Дуров"

    )



async def search(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
):


    query = update.message.text.strip()


    msg = await update.message.reply_text(
        "🔎 Ищу..."
    )


    results = search_duckduckgo(
        query
    )



    if not results:

        await msg.edit_text(
            "😕 Ничего не найдено"
        )

        return



    await msg.edit_text(
        "🔎 Найдено результатов:"
    )


    for result in results:


        title = html.escape(
            result["title"]
        )


        description = html.escape(
            result["description"]
        )


        url = result["url"]


        button = InlineKeyboardMarkup(

            [[

                InlineKeyboardButton(

                    "🌐 Открыть сайт",

                    url=url

                )

            ]]

        )


        text = (

            f"<b>{title}</b>\n\n"

        )


        if description:

            text += description



        await update.message.reply_text(

            text,

            parse_mode="HTML",

            reply_markup=button,

            disable_web_page_preview=True

        )



# =====================
# MAIN
# =====================


def main():


    threading.Thread(

        target=run_server,

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

        MessageHandler(

            filters.TEXT & ~filters.COMMAND,

            search

        )

    )


    print(
        "🤖 Бот запущен"
    )


    bot.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":

    main()
