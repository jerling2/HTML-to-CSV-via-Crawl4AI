import os
import shutil
from pathlib import Path


class Shell:
    __instance = None
    __base_paths = {}
    
    def __new__(cls, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            for key, value in kwargs.items():
                cls.__base_paths[key] = value
        return cls.__instance

    @staticmethod
    def mkdir(path):
        if not os.path.exists(path):
            os.mkdir(path)

    @staticmethod
    def rm_rf(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)

    @staticmethod
    def ls_files(path, glob_pattern="*", include_extention=True) -> [str]:
        if include_extention:
            return [item.name for item in Path(path).glob(glob_pattern) if item.is_file()]
        else:
            return [item.stem for item in Path(path).glob(glob_pattern) if item.is_file()]

    @staticmethod
    def ls_dirs(path, glob_pattern="*") -> [str]:
        return [item.name for item in Path(path).glob(glob_pattern) if item.is_dir()]

    @staticmethod
    def is_path_taken(path) -> bool:
        return os.path.exists(path)

    @staticmethod
    def basename(path) -> str:
        return os.path.basename(path)

    @classmethod
    def construct_path(cls, base_type, file_name, *extra_parts):
        base = cls.__base_paths.get(base_type, None)
        if base is None:
            raise Exception(f"Error: {base} path is not initialized in Shell")
        return os.path.join(base, file_name, *extra_parts)
