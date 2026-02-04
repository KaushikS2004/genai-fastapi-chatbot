def build_system_prompt(
    mode: str,
    format: str,
    tone: str
) -> str:
    prompt = """
You are a highly capable AI assistant.
Follow all instructions strictly.
Use Markdown formatting.
"""

    # 🎯 MODE CONTROL
    if mode == "coding":
        prompt += """
You are a senior software engineer.
- Provide correct, production-quality code
- Explain logic briefly
- Use code blocks
"""
    elif mode == "interview":
        prompt += """
You are an interview preparation assistant.
- Give clear, structured answers
- Highlight key points
- Be concise
"""
    elif mode == "explainer":
        prompt += """
You explain concepts to beginners.
- Use simple language
- Give examples
"""

    # 🧾 FORMAT CONTROL
    if format == "bullets":
        prompt += "\nAlways respond using bullet points."
    elif format == "table":
        prompt += "\nAlways respond using markdown tables."
    elif format == "json":
        prompt += "\nRespond ONLY in valid JSON. Do not include explanations."

    # 🎭 TONE CONTROL
    if tone == "simple":
        prompt += "\nKeep explanations very simple."
    elif tone == "detailed":
        prompt += "\nProvide detailed explanations."

    return prompt.strip()
