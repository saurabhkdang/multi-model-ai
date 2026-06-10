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
    
def get_view_columns(view_names: list[str]):
    if not view_names:
        return {}

    placeholders = ", ".join(["%s"] * len(view_names))

    query = f"""
    SELECT 
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name IN ({placeholders})
    ORDER BY table_name, ordinal_position
    """

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, view_names)
            rows = cursor.fetchall()

        schema = {}
        # print(rows)
        for row in rows:
            table = row["TABLE_NAME"]

            if table not in schema:
                schema[table] = []

            schema[table].append({
                "column": row["COLUMN_NAME"],
                "type": row["DATA_TYPE"]
            })

        return schema

    finally:
        connection.close()