def calculator_tool(query: str):
    try:
        allowed_chars = "0123456789+-*/(). "
        expression = "".join(ch for ch in query if ch in allowed_chars)

        if not expression.strip():
            return "No valid calculation found."

        result = eval(expression, {"__builtins__": {}})

        return f"Calculation result: {result}"

    except Exception as e:
        return f"Calculator error: {str(e)}"