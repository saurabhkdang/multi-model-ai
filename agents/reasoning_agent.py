import json
import re
import time
from core.logger import log_event
from llm_client import call_llm
from memory import update_memory_context


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found in reasoning response")

    return json.loads(match.group())

def extract_memory_context_with_llm(user_query: str, specialist_results: list):
    prompt = f"""
You are a memory context extractor for an HR chatbot.

Your job is to extract useful context for future follow-up questions.

User query:
{user_query}

Specialist agent results:
{json.dumps(specialist_results, default=str)}

Return ONLY valid JSON.

Required JSON format:
{{
  "last_employee": null or "employee name",
  "last_topic": null or "leave|attendance|salary|dob|work from home|policy|employee",
  "last_subject": null or "short subject",
  "should_update_memory": true or false
}}

Important rules:
1. If the query contains a person's name, extract it as last_employee.
2. A name may appear in possessive form, like "Saurabh's". In that case, last_employee should be "Saurabh".
3. If the query asks about leave balance, set:
   last_topic = "leave"
   last_subject = "leave balance"
   should_update_memory = true
4. If the query asks about attendance, set:
   last_topic = "attendance"
   last_subject = "attendance"
   should_update_memory = true
5. If the query asks about work from home or WFH, set:
   last_topic = "work from home"
   last_subject = "work from home policy"
   should_update_memory = true
6. If the query asks about policy, set:
   last_topic = "policy"
   last_subject = the specific policy if clear
   should_update_memory = true
7. Do not invent employee names.
8. If no useful follow-up context exists, set should_update_memory=false.

Examples:

User query: What is Saurabh's leave balance?
Output:
{{
  "last_employee": "Saurabh",
  "last_topic": "leave",
  "last_subject": "leave balance",
  "should_update_memory": true
}}

User query: Show Amit attendance last week
Output:
{{
  "last_employee": "Amit",
  "last_topic": "attendance",
  "last_subject": "attendance last week",
  "should_update_memory": true
}}

User query: Explain work from home policy
Output:
{{
  "last_employee": null,
  "last_topic": "work from home",
  "last_subject": "work from home policy",
  "should_update_memory": true
}}

User query: Hello
Output:
{{
  "last_employee": null,
  "last_topic": null,
  "last_subject": null,
  "should_update_memory": false
}}
"""

    raw = call_llm(prompt)

    try:
        return extract_json(raw)
    except Exception:
        return {
            "last_employee": None,
            "last_topic": None,
            "last_subject": None,
            "should_update_memory": False
        }

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
- If a requested agent has already returned useful data, do not request the same information again.
- If SQL_AGENT returned rows for the requested employee/topic, return FINAL.
- Only return NEED_MORE_INFO when no existing agent result can answer the user.

IMPORTANT:
- If requesting SQL_AGENT, do NOT write SQL query.
- SQL_AGENT input must always be natural language.
- BAD input: SELECT attendance_date FROM employee_attendance_leaves_status WHERE emp_name = 'Saurabh Dang'
- GOOD input: Get attendance records of Saurabh Dang

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

    memory_context = extract_memory_context_with_llm(
        user_query=user_query,
        specialist_results=specialist_results
    )

    if memory_context.get("should_update_memory"):
        update_memory_context(
            user_query=user_query,
            employee=memory_context.get("last_employee"),
            topic=memory_context.get("last_topic"),
            subject=memory_context.get("last_subject")
        )

    log_event("MEMORY_CONTEXT_UPDATED", {
        "request_id": request_id,
        "memory_context": memory_context
    })
    
    return extract_json(response)