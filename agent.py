import json
import re

from llm_client import call_llm
from tools.calculator import calculator_tool
from tools.text_summary import summary_tool
from tools.policy_search import policy_search_tool
from tools.general_llm import general_llm_tool
from memory import save_memory, get_memory


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found in LLM response")

    return json.loads(match.group())


def create_plan(user_query: str):
    prompt = f"""
You are an AI agent planner.

Choose the correct tool for the user query.

Available tools:

1. CALCULATOR
Use for math calculation questions.

2. SUMMARY
Use when user asks to summarize text.

3. POLICY_SEARCH
Use for HR policy questions about leave, attendance, or work from home.

4. MEMORY
Use MEMORY when:
- User wants you to remember something
- User asks previously stored information
Examples:

Remembering:

Input:
Remember my name is Saurabh

Output:

{{
 "tasks":[
   {{
     "tool":"MEMORY",
     "input":"name=Saurabh"
   }}
 ]
}}

Recalling:

Input:
What is my name?

Output:

{{
 "tasks":[
   {{
      "tool":"MEMORY",
      "input":"name"
   }}
 ]
}}

5. GENERAL_LLM

Use when:
- Other tools cannot answer
- General questions
- Fallback tool

Return JSON only.

{{
  "tasks":[
    {{
      "tool":"CALCULATOR | SUMMARY | POLICY_SEARCH | MEMORY | GENERAL_LLM",
      "input":"input for the selected tool"
    }}
  ]
}}

Multiple tasks are allowed.

User query:
{user_query}
"""

    response = call_llm(prompt)
    return extract_json(response)

def execute_tools(plan):

    results=[]

    for task in plan["tasks"]:

        tool=task["tool"]
        tool_input=task["input"]

        if tool=="CALCULATOR":

            output=calculator_tool(
                tool_input
            )

        elif tool=="SUMMARY":

            output=summary_tool(
                tool_input
            )

        elif tool=="POLICY_SEARCH":

            output=policy_search_tool(
                tool_input
            )

        elif tool == "MEMORY":
          if "=" in tool_input:
              key, value = tool_input.split("=", 1)
              output = save_memory(key.strip(), value.strip())
          else:
              output = get_memory(tool_input.strip())

        elif tool=="GENERAL_LLM":
            output=general_llm_tool(
                tool_input
            )

        else:

            output="Unknown tool"

        results.append({

            "tool":tool,
            "input":tool_input,
            "result":output

        })

    return results

def execute_tool1(plan: dict):
    tool = plan.get("tool")
    tool_input = plan.get("input", "")

    if tool == "CALCULATOR":
        return calculator_tool(tool_input)

    if tool == "SUMMARY":
        return summary_tool(tool_input)

    if tool == "POLICY_SEARCH":
        return policy_search_tool(tool_input)

    return "Unknown tool selected."

def run_agent(user_query: str):
    history = []
    max_steps = 3
    current_query = user_query

    for step in range(max_steps):
        plan = create_plan(current_query)

        tool_result = execute_tools(plan)

        reflection_prompt = f"""
You are an AI agent evaluator.

Original User Query:
{user_query}

Current Plan:
{plan}

Tool Result:
{tool_result}

Question:
Did the tool result successfully help answer the original user query?

Return ONLY one word:

GOOD

or

BAD
"""

        reflection = call_llm(reflection_prompt).strip().upper()

        history.append({
            "step": step + 1,
            "current_query": current_query,
            "plan": plan,
            "result": tool_result,
            "reflection": reflection
        })

        if "GOOD" in reflection:
            break

        if "BAD" in reflection:

            current_query = f"""
        Previous attempt failed.

        Original Query:

        {user_query}

        Previous Plan:

        {plan}

        Previous Result:

        {tool_result}

        IMPORTANT:

        Try another tool if previous tool failed.

        Create a better plan.
        """

            continue

        current_query = f"""
The previous tool result was not good.

Original user query:
{user_query}

Previous plan:
{plan}

Previous result:
{tool_result}

Rules:

- Never repeat failed tool
- Prefer specialized tools
- Use GENERAL_LLM only as last fallback

Create a better plan to answer the original query.
"""

    final_prompt = f"""
User Query:
{user_query}

Execution History:
{history}

Generate final answer in simple language.
"""

    answer = call_llm(final_prompt)

    return {
        "history": history,
        "answer": answer
    }

def run_agent2(user_query):

    history=[]

    max_steps=5

    current_query=user_query

    for step in range(max_steps):

        plan=create_plan(current_query)

        tool_result=execute_tools(plan)

        history.append({

            "step":step+1,
            "plan":plan,
            "result":tool_result

        })

        decision_prompt=f"""
User Query:

{user_query}

Execution History:

{history}

Should agent continue?

Return ONLY:

CONTINUE

or

STOP
"""

        decision=call_llm(
            decision_prompt
        ).strip().upper()

        if "STOP" in decision:

            break

        current_query=f"""
Previous results:

{tool_result}

Continue solving original query:

{user_query}
"""

    final_prompt=f"""
User Query:

{user_query}

Execution History:

{history}

Generate final answer.
"""

    answer=call_llm(
        final_prompt
    )

    return {

        "history":history,
        "answer":answer

    }

def run_agent1(user_query: str):
    plan = create_plan(user_query)
    tool_result = execute_tools(plan)

    final_prompt = f"""
User query:
{user_query}

Agent selected tool:
{plan}

Tool result:
{tool_result}

Give final answer to user in simple language.
"""

    final_answer = call_llm(final_prompt)

    return {
        "query": user_query,
        "plan": plan,
        "tool_result": tool_result,
        "answer": final_answer
    }