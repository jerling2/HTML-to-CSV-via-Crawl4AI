import asyncio
from src.utils import extract_from_local_file
from src.interface import Shell


class LocalExtractMode(Shell):
    def __init__(self, web_schema_path: str, data_path: str, json_out_path: str):
        super().__init__(
            web_schema_path=web_schema_path, 
            json_out_path=json_out_path, 
            data_path=data_path
        )

    def _prompt_web_schema(self) -> dict:
        available_schemas = self._ls(self.web_schema_path, "*.json")
        if not available_schemas:
            print("Uh oh, no available schemas")
            return
        user_input = input(f"Please choose a schema {available_schemas}: ")
        while user_input not in available_schemas:
            print("Invalid selection")
            user_input = input(f"Please choose a schema {available_schemas}: ")
        path = self._get_web_schema_file_path(user_input)
        try:
            return self._load_json(path)
        except Exception as e:
            print(f"Json Load Error: {e}")
            return None

    def _prompt_data(self) -> [str]:
        available_folders = self._ls_dir(self.data_path)
        user_input = input(f"Please choose a folder {available_folders}: ")
        while user_input not in available_folders:
            print("Invalid selection")
            user_input = input(f"Please choose a folder {available_folders}: ")
        path = self._get_data_folder_path(user_input)
        files = self._ls_file_uri(path)
        return files

    def _prompt_json_out(self) -> str:
        user_input = input(f"Please enter a name for the output folder: ")
        path = self._get_json_out_folder_path(user_input)
        while self._is_path_taken(path):
            if input("Name is taken. Overwrite [y]? ") == "y":
                self._rm_rf(path)
                break
            user_input = input(f"Please enter a name for the output folder: ")
            path = self._get_json_out_folder_path(user_input)
        self._mkdir(path)
        return user_input

    def interact(self):
        schema = self._prompt_web_schema()
        if not schema:
            return
        URIs = self._prompt_data()
        out_folder = self._prompt_json_out()
        page_num = 0
        for uri in URIs:
            json_data = asyncio.run(extract_from_local_file(uri, schema))
            if not json_data:
                continue
            out_path = self._get_json_out_file_path(out_folder, f'page {page_num}')
            self._dump_json_to_file(out_path, json_data)
            page_num += 1
        return