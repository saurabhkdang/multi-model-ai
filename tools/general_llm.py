from llm_client import call_llm


def general_llm_tool(query):

    prompt=f"""
Answer the user question.

Question:

{query}

Answer:
"""

    return call_llm(prompt)