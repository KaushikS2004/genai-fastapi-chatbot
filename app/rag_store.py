from app.vector_store import VectorStore

stores = {}

def get_store(user: str, conversation_id: str):
    key = (user, conversation_id)
    if key not in stores:
        stores[key] = VectorStore()
    return stores[key]
