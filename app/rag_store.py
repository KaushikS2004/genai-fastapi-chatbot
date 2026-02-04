from app.vector_store import VectorStore

stores = {}

def get_store(user: str, session_id: str):
    key = (user, session_id)
    if key not in stores:
        stores[key] = VectorStore()
    return stores[key]
