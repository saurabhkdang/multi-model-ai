from tools.general_llm import general_llm_tool
import time
from core.logger import log_event

def general_agent(task_input: str, request_id: str):
    start_time = time.time()

    log_event("AGENT_STARTED", {
        "request_id": request_id,
        "agent": "GENERAL_AGENT",
        "input": task_input
    })

    try:
        duration_ms = round((time.time() - start_time) * 1000, 2)

        log_event("AGENT_COMPLETED", {
            "request_id": request_id,
            "agent": "GENERAL_AGENT",
            "success": True,
            "duration_ms": duration_ms
        })
        return general_llm_tool(task_input)
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)

        log_event("AGENT_FAILED", {
            "request_id": request_id,
            "agent": "GENERAL_AGENT",
            "error": str(e),
            "duration_ms": duration_ms
        })

        return {
            "success": False,
            "error": str(e)
        }