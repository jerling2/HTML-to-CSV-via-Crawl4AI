# REF: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings
import ollama

def embed_texts(data: list[list[str]]):
    response = ollama.embed(
        model='nomic-embed-text',
        input=data
    )
    return response["embeddings"]