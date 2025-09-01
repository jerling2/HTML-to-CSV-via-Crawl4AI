import csv
from .string_transformer import Transformer
import json


def clean_extracted_content(table_schema, json_data):
    transformer = Transformer()
    entities = []
    for data in json_data:
        entities.extend(data.get(table_schema['selector'], []))        
    field_dict = table_schema['fields']
    for entity in entities:
        for field_name, field_props in field_dict.items():
            transformer_name = table_schema['transformers'].get(field_name, None)
            raw_text = entity.get(field_name, None)
            clean_text = transformer.apply_transformation(transformer_name, raw_text)
            if clean_text is None:
                continue
            if field_props.get('datatype', '') == "INT64":
                data = int(clean_text)
            else:
                data = clean_text 
            entity[field_name] = data
    return entities


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