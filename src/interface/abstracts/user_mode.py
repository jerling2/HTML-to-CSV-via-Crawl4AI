"""
Abstract class for all modes defined in ../modes
"""
from src.systems import (
    Shell,
    VectorDatabase
)


USER_STORAGE = {
    'schema_html': {
        'extention': '.json'
    },
    'schema_table': {
        'extention': '.json'
    },
    'data_content': {
        'nested': True,
        'extention': '.json',
    },
    'data_html': {
        'nested': True,
        'extention': '.html',
    },
    'data_table': {
        'extention': '.tsv'
    },
    'milvus': {
        'database': True
    }
}


class UserMode():

    def __init__(self, kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.shell = Shell(**kwargs)
        self.db = VectorDatabase()
    
    def get_path(self, storage_type, file_name=None, dir_name=None) -> str:
        if storage_type not in USER_STORAGE:
            raise Exception(f"Undefined `USER_STORAGE`: {storage_type}")
        if not USER_STORAGE[storage_type].get('nested', False) and dir_name:
            raise TypeError(f"Invalid use:`USER_STORAGE`: {storage_type}")
        if file_name and dir_name:
            return self.shell.construct_path(
                storage_type, 
                dir_name, 
                file_name + USER_STORAGE[storage_type]['extention']
            )
        if file_name:
            return self.shell.construct_path(
                storage_type, 
                file_name + USER_STORAGE[storage_type]['extention']
            )
        if dir_name:
            return self.shell.construct_path(
                storage_type, 
                dir_name
            )
        return self.shell.construct_path(storage_type, '')

    def ls(self, storage_type, dir_name=None, include_extention=True) -> [str]:
        if USER_STORAGE[storage_type].get('database', False):
            return self.db.list_collections()
        path = self.get_path(storage_type, dir_name=dir_name)
        if not dir_name and USER_STORAGE[storage_type].get('nested', False):
            return self.shell.ls_dirs(path)
        return self.shell.ls_files(path, "*" + USER_STORAGE[storage_type]['extention'], include_extention=include_extention)

    def _get_user_input_path(self, storage_type, user_input):
        if USER_STORAGE[storage_type].get('database', False):
            return user_input
        if USER_STORAGE[storage_type].get('nested', False):
            return self.get_path(storage_type, dir_name=user_input)
        return self.get_path(storage_type, file_name=user_input)

    def prompt_choose(self, storage_type, prompt_msg) -> str:
        available = self.ls(storage_type, include_extention=False)
        if not available:
            return None
        user_input = input(prompt_msg + f' {available}: ')
        while user_input not in available:
            print('Invalid selection')
            user_input = input(prompt_msg + f'{available}: ')
        return self._get_user_input_path(storage_type, user_input)
    
    def _is_path_taken(self, storage_type, path):
        if USER_STORAGE[storage_type].get('database', False):
            return self.db.is_name_taken(path)
        return self.shell.is_path_taken(path)

    def _remove(self, storage_type, path):
        if USER_STORAGE[storage_type].get('database', False):
            return self.db.drop_collection(path)
        if USER_STORAGE[storage_type].get('nested', False):
            return self.shell.rm_rf(path)

    def prompt_enter(self, storage_type, prompt_msg) -> str:
        user_input = input(prompt_msg + ": ").strip()
        while not user_input:
            print("Invalid name")
            user_input = input(prompt_msg + ": ").strip()
        path = self._get_user_input_path(storage_type, user_input)
        while self._is_path_taken(storage_type, path):
            if input("Name is taken. Overwrite [y]? ") == "y":
                self._remove(storage_type, path)
                break
            user_input = input(prompt_msg + ": ").strip()
            while not user_input:
                print("Invalid name")
                user_input = input(prompt_msg + ": ").strip()
            path = self._get_user_input_path(storage_type, user_input)
        if USER_STORAGE[storage_type].get('nested', False):
            self.shell.mkdir(path)
        return path

    def get_basename(self, path) -> str:
        return self.shell.basename(path)

    def get_paths_from_folder(self, storage_type, path_to_folder):
        dir_name = self.get_basename(path_to_folder)
        file_names =  self.ls(storage_type, dir_name=dir_name, include_extention=False)
        file_paths = [
            self.get_path(storage_type, dir_name=dir_name, file_name=file_name)
            for file_name in file_names
        ]
        return file_paths

    def interact(self):
        raise NotImplementedError("The 'interact' method must be implemented in concrete subclasses.")
