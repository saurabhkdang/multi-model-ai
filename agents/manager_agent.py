import json
import re

from llm_client import call_llm

from agents.memory_agent import memory_agent
from agents.general_agent import general_agent
from agents.reasoning_agent import reasoning_agent
from agents.sql_agent import sql_agent
from agents.vector_agent import vector_agent


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found in response")

    return json.loads(match.group())


def create_manager_plan(user_query: str):
    prompt = f"""
You are a manager agent.

You do not solve tasks yourself.
You assign tasks to specialist agents.

Available agents:

1. MEMORY_AGENT
Use to save or recall user memory.
For save, input must be key=value.
For recall, input must be key.

2. GENERAL_AGENT
Use only if no specialist agent fits.

3. SQL_AGENT
Use for employee database questions like leave balance, employee details, attendance, status, DOB, reporting manager.

4. VECTOR_AGENT
Use for work from home policy, buddy program and referral program document search.

Return ONLY JSON.

Format:

{{
 "tasks":[
   {{
     "agent":"MEMORY_AGENT | GENERAL_AGENT | SQL_AGENT | VECTOR_AGENT",
     "input":"input for specialist agent"
   }}
 ]
}}

User Query:

{user_query}
"""

    response = call_llm(prompt)
    return extract_json(response)


def run_specialist_agent(agent_name: str, task_input: str):
    if agent_name == "MEMORY_AGENT":
        return memory_agent(task_input)

    if agent_name == "GENERAL_AGENT":
        return general_agent(task_input)
    
    if agent_name == "SQL_AGENT":
      return sql_agent(task_input)

    if agent_name == "VECTOR_AGENT":
        return vector_agent(task_input)

    return "Unknown agent selected."


def run_manager_agent(user_query: str):
    plan = create_manager_plan(user_query)

    results = []

    for task in plan["tasks"]:
        agent_name = task["agent"]
        task_input = task["input"]

        output = run_specialist_agent(agent_name, task_input)

        results.append({
            "agent": agent_name,
            "input": task_input,
            "result": output
        })

    reasoning_result = reasoning_agent(
      user_query=user_query,
      manager_plan=plan,
      specialist_results=results
    )

    if reasoning_result.get("status") == "NEED_MORE_INFO":
        required_agent = reasoning_result.get("required_agent")
        extra_input = reasoning_result.get("input")

        extra_output = run_specialist_agent(
            required_agent,
            extra_input
        )

        results.append({
            "agent": required_agent,
            "input": extra_input,
            "result": extra_output,
            "requested_by": "REASONING_AGENT",
            "reason": reasoning_result.get("reason")
        })

        reasoning_result = reasoning_agent(
            user_query=user_query,
            manager_plan=plan,
            specialist_results=results
        )

    return {
        "plan": plan,
        "results": results,
        "reasoning": reasoning_result,
        "answer": reasoning_result.get("answer")
    }