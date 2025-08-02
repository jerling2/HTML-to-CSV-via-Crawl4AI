import json
from ..abstracts.user_mode import UserMode
from src.utils import generate_tsv


class ConvertJsonToTSVMode(UserMode):
    
    def interact(self, table_schema_path=None, content_data_path=None):
        if not table_schema_path:
            table_schema_path = self.prompt_choose('schema_table', "Please choose a table schema")
        if not table_schema_path:
            return print("No table schema files.")
        with open(table_schema_path, 'r') as f:
            table_schema = json.load(f)
        if not content_data_path:
            content_data_path = self.prompt_choose('data_content', "Please choose content data")
        if not content_data_path:
            return print("No content data.")
        content_data_folder = self.get_basename(content_data_path)
        files = self.ls('data_content', dir_name=content_data_folder, include_extention=False)
        paths = [self.get_path('data_content', dir_name=content_data_folder, file_name=file) for file in files]
        content = []
        for path in paths:
            with open(path, 'r') as f:
                try:
                    content.extend(json.load(f))
                except Exception as e:
                    return print(f"Unexpected error: {e}")
        table_out_path = self.prompt_enter('data_table', "Please enter a name for the output file")
        generate_tsv(table_schema, content, table_out_path)