import json
from ..abstracts.user_mode import UserMode
from src.utils import clean_extracted_content, normalize_entity_data

class DevMode(UserMode):

    def interact(self):
        table_schema_path = self.prompt_choose('schema_table', "Please choose a table schema")
        with open(table_schema_path, "r") as f:
            table_schema = json.load(f)

        # --- I'm skipping to the content for this demo.

        example_content_path = self.prompt_choose('data_content', "Please choose a data folder")
        example_content_folder = self.get_basename(example_content_path)
        example_path = self.get_path(storage_type='data_content', dir_name=example_content_folder, file_name='page_0')
        with open(example_path, "r") as f:
            extracted_content = json.load(f)

        # --- --- ---  --- --- ---  --- --- ---  - #
        # --- The Post Data Collection Process --- #
        entity_data = clean_extracted_content(table_schema, extracted_content)
        normalize_entity_data(table_schema, entity_data)        
        
        # now the data is ready to be inserted into the data base
        collection_name = self.prompt_choose('milvus', "Please choose a collection")
        self.db.load_collection(collection_name)
        self.db.upsert(collection_name, entity_data)
        self.db.release_collection(collection_name)

        # Incrementally fetch data from the database
        """
        Since there's at most a few hundred enttites, it's easy enough to hold all the data in memory.
        For larger databases, it's possible to do work on 'batches' of entiteis.
        """
        self.db.load_collection(collection_name)
        fetched_data = []
        offset = 0
        batch_size=10
        while (res := self.db.query(collection_name, filter="job_id >= 0", offset=offset, limit=batch_size, output_fields=['*'])):
            fetched_data.extend(res)
            offset += batch_size
        self.db.release_collection(collection_name)

        # (Then update the data)
        # Update the records (use `upsert` = 'Update' or 'Insert')
        # --- DONE