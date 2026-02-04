def build_messages(system_prompt: str, history: list, user_prompt: str):
    messages = []

    # system prompt
    messages.append({
        "role": "system",
        "content": system_prompt
    })

    # chat history
    for msg in history:
        messages.append(msg)

    # current user prompt
    messages.append({
        "role": "user",
        "content": user_prompt
    })

    return messages
