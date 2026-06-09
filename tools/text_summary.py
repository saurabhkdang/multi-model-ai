from llm_client import call_llm


def summary_tool(text: str):
    prompt = f"""
Summarize the following text in simple language:

{text}
"""
    return call_llm(prompt)