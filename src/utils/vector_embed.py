import ollama

def embed_texts(data: list[list[str]]):
    response = ollama.embed(
        model='nomic-embed-text',
        input=data
    )
    return response["embeddings"]