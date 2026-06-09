import os
import pymysql
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )


def run_sql(query: str):
    if not query.strip().lower().startswith("select"):
        return {
            "error": "Only SELECT queries are allowed."
        }

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        connection.close()

        return rows

    except Exception as e:
        return {
            "error": str(e)
        }