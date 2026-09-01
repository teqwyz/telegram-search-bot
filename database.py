import sqlite3
from datetime import datetime


DB_NAME = "bot.db"


# =====================
# ПОДКЛЮЧЕНИЕ
# =====================

def connect():

    return sqlite3.connect(
        DB_NAME
    )



# =====================
# СОЗДАНИЕ БАЗЫ
# =====================

def init_db():

    db = connect()
    cursor = db.cursor()


    # пользователи

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY,

        username TEXT,

        first_name TEXT,

        last_name TEXT,

        created TIMESTAMP

    )
    """)



    # история поиска

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        query TEXT,

        created TIMESTAMP

    )
    """)



    db.commit()

    db.close()





# =====================
# ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ
# =====================

def add_user(user):

    db = connect()

    cursor = db.cursor()


    cursor.execute(
        """
        INSERT OR IGNORE INTO users

        (
            id,
            username,
            first_name,
            last_name,
            created
        )

        VALUES (?,?,?,?,?)
        """,

        (

            user.id,

            user.username,

            user.first_name,

            user.last_name,

            datetime.now()

        )

    )


    db.commit()

    db.close()







# =====================
# СОХРАНЕНИЕ ПОИСКА
# =====================

def add_history(
    user_id,
    query
):

    db = connect()

    cursor = db.cursor()



    cursor.execute(
        """
        INSERT INTO history

        (
            user_id,
            query,
            created
        )

        VALUES (?,?,?)

        """,

        (

            user_id,

            query,

            datetime.now()

        )

    )


    db.commit()

    db.close()







# =====================
# ПОЛУЧЕНИЕ ИСТОРИИ
# =====================

def get_history(
    user_id,
    limit=10
):

    db = connect()

    cursor = db.cursor()



    cursor.execute(
        """
        SELECT query

        FROM history

        WHERE user_id=?

        ORDER BY id DESC

        LIMIT ?

        """,

        (

            user_id,

            limit

        )

    )



    rows = cursor.fetchall()



    db.close()



    return [

        row[0]

        for row in rows

    ]









# =====================
# СТАТИСТИКА
# =====================

def count_users():

    db = connect()

    cursor = db.cursor()



    cursor.execute(
        """
        SELECT COUNT(*)

        FROM users

        """
    )


    result = cursor.fetchone()[0]


    db.close()


    return result







def count_searches():

    db = connect()

    cursor = db.cursor()



    cursor.execute(
        """
        SELECT COUNT(*)

        FROM history

        """
    )


    result = cursor.fetchone()[0]


    db.close()


    return result
