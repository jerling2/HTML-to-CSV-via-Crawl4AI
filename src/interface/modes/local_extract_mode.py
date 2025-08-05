import asyncio
import json
from ..abstracts.user_mode import UserMode
from .json_to_tsv_mode import ConvertJsonToTSVMode
from src.utils import Agent


class LocalExtractMode(UserMode):

    def __init__(self):
        super().__init__()
        self.agent = Agent()

    def interact(self, html_schema_path=None, html_data_path=None):
        if not html_schema_path:
            html_schema_path = self.prompt_choose('schema_html', "Please choose a html schema")
        if not html_schema_path:
            return print("No available html schemas.")
        with open(html_schema_path, 'r') as f:
            schema = json.load(f)
        if not html_data_path:
            html_data_path = self.prompt_choose('data_html', "Please choose html data")
        if not html_data_path:
            return print("No available html data.")
        html_data_folder = self.get_basename(html_data_path)
        files = self.ls('data_html', dir_name=html_data_folder, include_extention=False)
        paths = ['file://' + self.get_path('data_html', dir_name=html_data_folder, file_name=file) for file in files]
        content_out_path = self.prompt_enter('data_content', "Please enter a name for the output folder")
        content_out_folder = self.get_basename(content_out_path)
        page_num = 0
        for path in paths:
            result = asyncio.run(
                self.agent.extract_from_local_file(path, schema)
            )
            if not result:
                continue
            out_path = self.get_path('data_content', file_name=f'page_{page_num}', dir_name=content_out_folder)
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2)
            page_num += 1
        if input('Continue to table [y]? ') == "y":
            program = ConvertJsonToTSVMode()
            program.interact(content_data_path=content_out_path)
