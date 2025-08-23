from pymilvus import MilvusClient, DataType


class VectorDatabase:

    def __init__(self, collection_name):
        self.client = MilvusClient(
            uri="http://localhost:19530",
            token="root:Milvus"
        )
        self.collection_name = collection_name

    def __enter__(self):
        self.client.load_collection(
            collection_name=self.collection_name
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.release_collection(
            collection_name=self.collection_name
        )
        if exc_type:
            print(f"An exception occurred: {exc_val}")
        return False
