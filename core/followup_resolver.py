import re
import json
from core.logger import log_event
from llm_client import call_llm


def resolve_followup_query(user_query: str, memory_context: dict, request_id: str):
    prompt = f"""
You are a follow-up query resolver for an HR chatbot.

Your job:
Decide whether the current user query depends on previous context.

Previous context:
{json.dumps(memory_context, indent=2)}

Current user query:
{user_query}

Rules:
1. If the query is already complete, return it unchanged.
2. If the query uses words like it, this, that, his, her, same, previous, related to it, resolve it using previous context.
3. If previous context is not enough, keep the query unchanged.
4. Do not invent employee names.
5. Do not invent HR topics.
6. Return only valid JSON.

Output format:
{{
  "is_followup": true/false,
  "resolved_query": "...",
  "reason": "short reason"
}}
"""

    raw = call_llm(prompt)

    try:
        data = extract_json(raw)
    except Exception:
        log_event("FOLLOWUP_RESOLVE_FAILED", {
            "request_id": request_id,
            "raw_response": raw
        })

        return {
            "is_followup": False,
            "resolved_query": user_query,
            "reason": "LLM response parsing failed"
        }

    log_event("FOLLOWUP_RESOLVED", {
        "request_id": request_id,
        "original_query": user_query,
        "resolved_query": data.get("resolved_query"),
        "is_followup": data.get("is_followup"),
        "reason": data.get("reason")
    })

    return data

def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group())