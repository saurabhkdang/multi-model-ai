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


def save_memory(key: str, value: str):
    memory_data = load_memory()

    memory_data[key.lower()] = value

    save_all_memory(memory_data)

    return f"Saved {key}: {value}"


def get_memory(key: str):
    memory_data = load_memory()

    return memory_data.get(
        key.lower(),
        "I don't have that information yet."
    )