from openai import OpenAI

client = OpenAI()

def embed_texts(texts: list[str]):
    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [d.embedding for d in res.data]

def embed_query(query: str):
    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return res.data[0].embedding
