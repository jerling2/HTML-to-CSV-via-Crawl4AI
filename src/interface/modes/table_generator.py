import json
import csv
from src.interface import UserMode


class ConvertJsonToCSVMode(UserMode):
    
    def _generate_tsv(self, schema, json_data, out_path):
        selection = []
        for data in json_data:
            selection.extend(data.get(schema['selector'], []))            
        headers = schema['headers']
        rows = [headers]
        for item in selection:
            row = []
            for header in headers:
                filter_name = schema['filters'].get(header)
                filter_fun = FILTER_MAP.get(filter_name, NOOP)
                string = filter_fun(item.get(header, ""))
                row.append(string)
            rows.append(row)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerows(rows)

    def interact(self):
        table_schema_path = self.prompt_choose('schema_table', "Please choose a schema")
        if not table_schema_path:
            return print("No table schema files.")
        with open(table_schema_path, 'r') as f:
            table_schema = json.load(f)
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
        self._generate_tsv(table_schema, content, table_out_path)


def NOOP(text: str) -> str:
    return text


def handshake_extend_href(text: str) -> str:
    result = "https://uoregon.joinhandshake.com" + text
    return result


def handshake_extract_pay(text: str) -> str:
    tokens = text.split('\u00b7')
    filtered = list(filter(lambda t: "/" in t, tokens))
    if not filtered:
        return "N/A"
    return filtered[0].strip()


def handshake_extract_type(text: str) -> str:
    tokens = text.split('\u00b7')
    check = ["Part-time", "Full-time", "Internship"]
    filtered = list(filter(lambda t: any(word in t for word in check), tokens))
    if not filtered:
        return "N/A"
    return filtered[0].strip()


def handshake_extract_duration(text: str) -> str:
    tokens = text.split('\u00b7')
    filtered = list(filter(lambda t: "\u2014" in t, tokens))
    if not filtered:
        return "N/A"
    return filtered[0].strip()


def handshake_extract_location(text: str) -> str:
    tokens = text.split('\u00b7')
    if not tokens:
        return "N/A"
    return tokens[0]


def handshake_extract_deadline(text: str) -> str:
    tokens = text.split('\u00b7')
    if len(tokens) < 2:
        return "N/A"
    return tokens[1]


FILTER_MAP = {
    "handshake_extend_href": handshake_extend_href,
    "handshake_extract_pay": handshake_extract_pay,
    "handshake_extract_type": handshake_extract_type,
    "handshake_extract_duration": handshake_extract_duration,
    "handshake_extract_location": handshake_extract_location,
    "handshake_extract_deadline": handshake_extract_deadline
}