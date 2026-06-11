from memory import save_memory, get_memory
import time
from core.logger import log_event


def memory_agent(task_input: str, request_id: str):
    start_time = time.time()

    log_event("AGENT_STARTED", {
        "request_id": request_id,
        "agent": "MEMORY_AGENT",
        "input": task_input
    })

    try:
        if "=" in task_input:
            key, value = task_input.split("=", 1)
            return save_memory(key.strip(), value.strip())
        
        duration_ms = round((time.time() - start_time) * 1000, 2)

        log_event("AGENT_COMPLETED", {
            "request_id": request_id,
            "agent": "MEMORY_AGENT",
            "success": True,
            "duration_ms": duration_ms
        })

        return get_memory(task_input.strip())
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)

        log_event("AGENT_FAILED", {
            "request_id": request_id,
            "agent": "MEMORY_AGENT",
            "error": str(e),
            "duration_ms": duration_ms
        })

        return {
            "success": False,
            "error": str(e)
        }