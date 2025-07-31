import json
import os
import shutil
from pathlib import Path


class Shell:
    def __init__(self,
        web_schema_path=None, 
        data_path=None,
        json_out_path=None,
        table_schema_path=None,
        tsv_out_path=None
    ):
        self.web_schema_path = web_schema_path
        self.data_path = data_path
        self.json_out_path = json_out_path
        self.table_schema_path = table_schema_path
        self.tsv_out_path = tsv_out_path

    @staticmethod
    def _load_json(path_to_json):
        json_data = None
        with open(path_to_json, "r") as file:
            json_data = json.load(file)
        return json_data

    @staticmethod
    def _dump_json_to_file(path, json_data):
        with open(path, 'w') as f:
            json.dump(json_data, f, indent=2)

    @staticmethod
    def _ls(path, glob_pattern="*") -> [str]:
        result = []
        for item in Path(path).glob(glob_pattern):
            item_name_without_extension = item.stem
            result.append(item_name_without_extension)
        return result

    @staticmethod
    def _rm_rf(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)

    @staticmethod
    def _mkdir(path):
        if not os.path.exists(path):
            os.mkdir(path)

    @staticmethod
    def _ls_dir(path) -> [str]:
        return [item.name for item in Path(path).iterdir() if item.is_dir()]

    @staticmethod
    def _ls_file_uri(path) -> [str]:
        result = []
        for item in Path(path).iterdir():
            if not item.is_file():
                continue
            absolute_path = item.resolve()
            result.append(absolute_path.as_uri())
        return result

    @staticmethod
    def _is_path_taken(path):
        return os.path.exists(path)

    def _get_web_schema_file_path(self, filename):
        return os.path.join(self.web_schema_path, filename + ".json")

    def _get_table_schema_file_path(self, filename):
        return os.path.join(self.table_schema_path, filename + ".json")

    def _get_data_folder_path(self, dirname):
        return os.path.join(self.data_path, dirname)

    def _get_json_out_folder_path(self, dirname):
        return os.path.join(self.json_out_path, dirname)

    def _get_json_out_file_path(self, dirname, filename):
        return os.path.join(self.json_out_path, dirname, filename + ".json")

    def _get_tsv_out_path(self, filename):
        return os.path.join(self.tsv_out_path, filename + ".tsv")