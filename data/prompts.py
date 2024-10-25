IMPROVEMENT_PROMPT = """
Your task is to enhance the following code by:
1. Addressing the issues identified by the linter.
2. Applying formatting fixes suggested by the formatter.
3. Making overall improvements in terms of efficiency and readability.
Provided Issues:
{issues}

Formatted Code:
{formatted_code}

Adjust the provided code accordingly and ensure clarity and maintainability.
"""
