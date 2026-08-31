import sqlite3
from datetime import datetime


DATABASE = "bot.db"



# =====================
# CONNECTION
# =====================

def connect():

    return sqlite3.connect(
        DATABASE
    )





# =====================
# INIT DATABASE
# =====================

def init_db():

    conn = connect()

    cursor = conn.cursor()



    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users(

            user_id INTEGER PRIMARY KEY,

            username TEXT,

            created TEXT

        )
        """
    )



    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS history(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            query TEXT,

            created TEXT

        )
        """
    )



    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stats(

            name TEXT PRIMARY KEY,

            value INTEGER DEFAULT 0

        )
        """
    )



    conn.commit()

    conn.close()





# =====================
# USERS
# =====================

def add_user(user):

    conn = connect()

    cursor = conn.cursor()



    cursor.execute(

        """
        INSERT OR IGNORE INTO users

        (
            user_id,
            username,
            created
        )

        VALUES(?,?,?)

        """,

        (

            user.id,

            user.username,

            str(datetime.now())

        )

    )



    conn.commit()

    conn.close()





def count_users():

    conn = connect()

    cursor = conn.cursor()



    cursor.execute(

        "SELECT COUNT(*) FROM users"

    )


    result = cursor.fetchone()[0]


    conn.close()


    return result





# =====================
# HISTORY
# =====================

def add_history(
    user_id,
    query
):

    conn = connect()

    cursor = conn.cursor()



    cursor.execute(

        """

        INSERT INTO history

        (

            user_id,

            query,

            created

        )

        VALUES(?,?,?)

        """,

        (

            user_id,

            query,

            str(datetime.now())

        )

    )



    conn.commit()

    conn.close()





def get_history(
    user_id
):

    conn = connect()

    cursor = conn.cursor()



    cursor.execute(

        """

        SELECT query

        FROM history

        WHERE user_id=?

        ORDER BY id DESC

        LIMIT 20

        """,

        (

            user_id,

        )

    )



    data = cursor.fetchall()



    conn.close()



    return [

        item[0]

        for item in data

    ]





def count_searches():

    conn = connect()

    cursor = conn.cursor()



    cursor.execute(

        "SELECT COUNT(*) FROM history"

    )



    result = cursor.fetchone()[0]


    conn.close()


    return result
