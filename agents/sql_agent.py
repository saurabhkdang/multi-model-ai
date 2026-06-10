import json
import re
from llm_client import call_llm
from db import run_sql, get_db_connection, get_view_columns

TABLE_INFO = {
    "employees": "this is the table having all employees",
    "employee_attendance_leaves_status" : "table to have all employee attendance status of all days",
    "employees_job_details" : "table to have all data related to employee job details"
}

ALLOWED_VIEWS = list(TABLE_INFO.keys())


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found")

    return json.loads(match.group())


def extract_sql(text: str):
    text = text.replace("```sql", "").replace("```", "").strip()

    match = re.search(r"select .*", text, re.IGNORECASE | re.DOTALL)

    if not match:
        raise ValueError("No SELECT query found")

    sql = match.group().strip().rstrip(";")

    return sql


def is_safe_sql(sql: str):
    sql_lower = sql.lower().strip()

    blocked = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "truncate ",
        "create ",
        "replace ",
        "grant ",
        "revoke "
    ]

    if not sql_lower.startswith("select"):
        return False

    for word in blocked:
        if word in sql_lower:
            return False

    return True


def detect_views(question: str):
    prompt = f"""
You are a database view selector.

Select the most relevant database view or views for the user question.

Return ONLY JSON.

Format:

{{
  "views": ["view_name"]
}}

Rules:
- Only choose from the available views
- Multiple views are allowed only if needed
- Do not invent view names

Available views:

{TABLE_INFO}

User Question:

{question}
"""

    response = call_llm(prompt)
    data = extract_json(response)

    views = data.get("views", [])

    valid_views = [
        view for view in views
        if view in ALLOWED_VIEWS
    ]

    if not valid_views:
        raise ValueError("No valid view selected")

    return valid_views

def get_selected_schema(views):
    schema_data = get_view_columns(views)

    schema_parts = []

    for view_name, columns in schema_data.items():
        column_lines = []

        for col in columns:
            column_lines.append(
                f"- {col['column']} ({col['type']})"
            )

        schema_parts.append(
            f"""
View: {view_name}

Columns:
{chr(10).join(column_lines)}
"""
        )

    return "\n\n".join(schema_parts)

def get_selected_schema1(views):
    connection = get_db_connection()

    cursor = connection.cursor()

    schema_info = ""

    for table in views:

        # GET CREATE TABLE / VIEW
        cursor.execute(f"SHOW CREATE TABLE {table}")

        result = cursor.fetchone()

        create_statement = list(result.values())[1]

        schema_info += f"\n\n{create_statement}"

    connection.close()

    return schema_info


def generate_sql(question: str, schema: str):
    prompt = f"""
You are a MySQL SQL generator.

Generate ONE safe SELECT query only.

Rules:
- Return only SQL
- Only use the provided schema
- Only SELECT queries allowed
- Do not use SELECT *
- Use clear column names
- Use LIKE for employee name matching
- Use aliases when needed
- Add LIMIT 10 unless user asks for all
- For dates, use YYYY-MM-DD format
- For month queries, use DATE_FORMAT(date_column, '%Y-%m') if needed
- Do not invent columns
- Do not invent tables or views

Provided Schema:

{schema}

User Question:

{question}
"""

    response = call_llm(prompt)
    sql = extract_sql(response)

    if not is_safe_sql(sql):
        raise ValueError("Unsafe SQL generated")

    return sql


def sql_agent(task_input: str):
    try:
        views = detect_views(task_input)
        schema = get_selected_schema(views)
        
        sql = generate_sql(
            question=task_input,
            schema=schema
        )

        result = run_sql(sql)

        return {
            "views": views,
            "sql": sql,
            "result": result
        }

    except Exception as e:
        return {
            "error": str(e)
        }