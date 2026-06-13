import time
import json
import re

from core.logger import log_event
from llm_client import call_llm
from memory import save_memory, get_memory, update_memory_context, get_memory_context


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found")

    return json.loads(match.group())


def extract_memory_with_llm(task_input: str):
    prompt = f"""
You are a memory extractor for an HR chatbot.

Extract memory facts from the user input.

User input:
{task_input}

Return ONLY valid JSON.

Format:
{{
  "employee_name": null or "employee name",
  "last_topic": null or "leave|attendance|salary|dob|work from home|policy|employee",
  "last_subject": null or "short subject"
}}

Rules:
- If user says remember employee name is X, employee_name should be X.
- If input contains "his" or "her" and employee name is not given, keep employee_name null.
- Do not invent employee names.
"""

    raw = call_llm(prompt)
    data = extract_json(raw)

    return data


def memory_agent(task_input: str, request_id: str):
    start_time = time.time()

    log_event("AGENT_STARTED", {
        "request_id": request_id,
        "agent": "MEMORY_AGENT",
        "input": task_input
    })

    try:
        q = task_input.lower()

        if "=" in task_input:
            key, value = task_input.split("=", 1)
            result = save_memory(key.strip(), value.strip())

        elif "remember" in q or "save" in q:
            extracted = extract_memory_with_llm(task_input)

            update_memory_context(
                user_query=task_input,
                employee=extracted.get("employee_name"),
                topic=extracted.get("last_topic"),
                subject=extracted.get("last_subject")
            )

            result = {
                "message": "Memory updated",
                "memory": get_memory_context()
            }

        else:
            result = get_memory_context()

        duration_ms = round((time.time() - start_time) * 1000, 2)

        log_event("AGENT_COMPLETED", {
            "request_id": request_id,
            "agent": "MEMORY_AGENT",
            "success": True,
            "duration_ms": duration_ms,
            "result": result
        })

        return {
            "success": True,
            "result": result
        }

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