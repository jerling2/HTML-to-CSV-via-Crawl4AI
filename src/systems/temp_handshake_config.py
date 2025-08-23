"""
Run `python3 src/database/handshake_config.py`
"""
from pymilvus import MilvusClient, DataType

client = MilvusClient(
    uri="http://localhost:19530",
    token="root:Milvus"
)

# --- create the schema ---
schema = MilvusClient.create_schema()
schema.add_field( field_name="id",       datatype=DataType.INT64, is_primary=True, auto_id=True )
schema.add_field( field_name="company",  datatype=DataType.VARCHAR, max_length=512 )
schema.add_field( field_name="position", datatype=DataType.VARCHAR, max_length=512 )
schema.add_field( field_name="pay",      datatype=DataType.VARCHAR, max_length=512 )
schema.add_field( field_name="type",     datatype=DataType.VARCHAR, max_length=512 )
schema.add_field( field_name="location", datatype=DataType.VARCHAR, max_length=512 )
schema.add_field( field_name="vector",   datatype=DataType.FLOAT_VECTOR, dim=768 )

# --- create indices ---
index_params = client.prepare_index_params()
index_params.add_index( field_name="vector",  index_type="AUTOINDEX", metric_type="COSINE" )

# --- create collection ---
client.create_collection( collection_name="handshake", schema=schema, index_params=index_params )