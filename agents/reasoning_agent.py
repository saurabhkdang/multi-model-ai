import json
import re
import time
from core.logger import log_event
from llm_client import call_llm


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found in reasoning response")

    return json.loads(match.group())


def reasoning_agent(user_query, manager_plan, specialist_results, request_id: str):
    start_time = time.time()

    log_event("REASONING_STARTED", {
        "request_id": request_id,
        "user_query": user_query,
        "tasks_completed": [
            {
                "agent": item["agent"],
                "input": item["input"]
            }
            for item in specialist_results
        ]
        # "available_results": list(specialist_results.keys())
    })

    prompt = f"""
You are a reasoning agent.

Your job:
1. Understand original user query
2. Analyze specialist results
3. Decide if enough information is available
4. Either return final answer or request one more agent call

Available agents:
- MEMORY_AGENT
- VECTOR_AGENT
- SQL_AGENT
- GENERAL_AGENT

Rules:

- Do not request another agent if the missing information does not exist.
- Do not call GENERAL_AGENT for user-specific facts that are unavailable.
- Only request another agent when that agent can realistically provide new information.

Return ONLY JSON.

If enough information is available:

{{
  "status": "FINAL",
  "answer": "final answer here"
}}

If more information is needed:

{{
  "status": "NEED_MORE_INFO",
  "required_agent": "AGENT_NAME",
  "input": "input for agent",
  "reason": "why this agent is needed"
}}

Original User Query:
{user_query}

Manager Plan:
{manager_plan}

Specialist Results:
{specialist_results}
"""

    response = call_llm(prompt)

    duration_ms = round((time.time() - start_time) * 1000, 2)

    log_event("REASONING_COMPLETED", {
        "request_id": request_id,
        # "used_results": list(specialist_results.keys()),
        "tasks_completed": [
            {
                "agent": item["agent"],
                "input": item["input"]
            }
            for item in specialist_results
        ],
        "duration_ms": duration_ms
    })
    
    return extract_json(response)