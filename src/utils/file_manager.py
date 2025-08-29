import csv
from .string_transformer import Transformer
import json


def clean_extracted_content(table_schema, json_data):
    transformer = Transformer()
    entities = []
    for data in json_data:
        entities.extend(data.get(table_schema['selector'], []))        
    fields = table_schema['fields']
    for entity in entities:
        for field in fields:
            transformer_name = table_schema['transformers'].get(field, None)
            raw_text = entity.get(field, "")
            modified_text = transformer.apply_transformation(transformer_name, raw_text)
            entity[field] = modified_text
    return entities


def normalize_entity_data(table_schema, entity_data):
    fields = table_schema['fields']
    for entity in entity_data:
        for field_name, field_props in fields.items():
            data = entity.get(field_name, None)
            datatype = field_props.get('datatype', '')
            dim = field_props.get('dim', 0)
            if data and datatype == "INT64":
                entity[field_name] = int(data)
            if not data and datatype == "FLOAT_VECTOR":
                entity[field_name] = [0] * dim #< Dummy vector to satisfy Milvus vector requirement


"""
Depreciated (transitioning to Milvus database instead of using the file system)
"""
def generate_tsv(schema, json_data, out_path):
    transformer = Transformer()
    selection = []
    for data in json_data:
        selection.extend(data.get(schema['selector'], []))            
    headers = schema['headers']
    rows = [headers]
    for item in selection:
        row = []
        for header in headers:
            transformer_name = schema['transformers'].get(header, None)
            raw_text = item.get(header, "")
            modified_text = transformer.apply_transformation(transformer_name, raw_text)
            row.append(modified_text)
        rows.append(row)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(rows)