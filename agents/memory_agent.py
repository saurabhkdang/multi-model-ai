from memory import save_memory, get_memory


def memory_agent(task_input: str):
    if "=" in task_input:
        key, value = task_input.split("=", 1)
        return save_memory(key.strip(), value.strip())

    return get_memory(task_input.strip())