from typing import Dict, List, Tuple

# Key = (user_id, session_id)
# Value = list of messages
chat_sessions: Dict[Tuple[str, str], List[dict]] = {}


def get_history(user_id: str, session_id: str) -> List[dict]:
    return chat_sessions.get((user_id, session_id), [])


def save_message(user_id: str, session_id: str, role: str, content: str):
    key = (user_id, session_id)
    chat_sessions.setdefault(key, []).append({
        "role": role,
        "content": content
    })


def clear_history(user_id: str, session_id: str):
    chat_sessions.pop((user_id, session_id), None)
