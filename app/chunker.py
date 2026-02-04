import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, max_tokens=300, overlap=50):
    tokens = enc.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk = enc.decode(tokens[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks
