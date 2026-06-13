import json
from pathlib import Path

MEMORY_FILE = Path("data/memory.json")


def load_memory():
    if not MEMORY_FILE.exists():
        return {}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_all_memory(memory_data):
    MEMORY_FILE.parent.mkdir(exist_ok=True)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory_data, f, indent=2)


def get_memory_context():
    memory = load_memory()

    return {
        "last_query": memory.get("last_query"),
        "last_employee": memory.get("last_employee") or memory.get("employee_name"),
        "last_topic": memory.get("last_topic"),
        "last_subject": memory.get("last_subject") or memory.get("current_focus"),
        "employee_name": memory.get("employee_name")
    }


def update_memory_context(
    user_query: str = None,
    employee: str = None,
    topic: str = None,
    subject: str = None
):
    memory = load_memory()

    if user_query:
        memory["last_query"] = user_query

    if employee:
        memory["last_employee"] = employee
        memory["employee_name"] = employee

    if topic:
        memory["last_topic"] = topic

    if subject:
        memory["last_subject"] = subject
        memory["current_focus"] = subject

    save_all_memory(memory)


def save_memory(key: str, value: str):
    memory_data = load_memory()

    clean_key = key.strip().lower().replace(" ", "_")

    memory_data[clean_key] = value

    if clean_key in ["employee", "employee_name", "name"]:
        memory_data["employee_name"] = value
        memory_data["last_employee"] = value

    save_all_memory(memory_data)

    return f"Saved {clean_key}: {value}"


def get_memory(key: str):
    memory_data = load_memory()
    clean_key = key.strip().lower().replace(" ", "_")

    return memory_data.get(
        clean_key,
        "I don't have that information yet."
    )