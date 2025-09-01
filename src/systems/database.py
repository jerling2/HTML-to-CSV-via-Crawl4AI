import os
import json
from pymilvus import MilvusClient, DataType


class VectorDatabase:
    __instance = None
    __client = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__client = MilvusClient(
                uri=os.getenv("MILVUS_URI"),
                token=os.getenv("MILVUS_TOK")
            )
        return cls.__instance

    @staticmethod
    def _load_config(json_path):
        with open(json_path) as f:
            config = json.load(f)
        for field_dict in config['fields'].values():
            if (data_type := field_dict.get('datatype', None)):
                field_dict['datatype'] = DataType[data_type]
        return config

    @staticmethod
    def _load_schema(config): # -> schema
        schema = MilvusClient.create_schema()
        for name, attributes in config['fields'].items():
            schema.add_field(field_name=name, **attributes)
        return schema

    def _load_index_params(cls, config): # -> index_params
        index_params = cls.__client.prepare_index_params()
        for name, attributes in config['indices'].items():
            index_params.add_index(field_name=name,  index_type="AUTOINDEX", metric_type="COSINE" )
        return index_params
    
    def create_collection(cls, collection_name, json_path):
        config = cls._load_config(json_path)
        schema = cls._load_schema(config)
        index_params = cls._load_index_params(config)
        cls.__client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params
        )

    def drop_collection(cls, collection_name):
        cls.__client.drop_collection(
            collection_name=collection_name
        )

    def is_name_taken(cls, name):
        return name in cls.list_collections()

    def load_collection(cls, collection_name):
        cls.__client.load_collection(
            collection_name=collection_name
        )

    def release_collection(cls, collection_name):
        cls.__client.release_collection(
            collection_name=collection_name
        )

    def list_collections(cls):
        return cls.__client.list_collections()

    def describe_collection(cls, collection_name):
        return cls.__client.describe_collection(
            collection_name=collection_name
        )

    def upsert(cls, collection_name, data):
        return cls.__client.upsert(
            collection_name=collection_name,
            data=data
        )

    def insert(cls, collection_name, data):
        return cls.__client.insert(
            collection_name=collection_name,
            data=data
        )

    def query(cls, collection_name, **kwargs):
        return cls.__client.query(
            collection_name=collection_name,
            **kwargs
        )

