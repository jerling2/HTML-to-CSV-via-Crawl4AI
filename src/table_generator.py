from src.shell import Shell
import csv


FILTER_MAP = {
    "handshake_extend_href": handshake_extend_href,
    "handshake_extract_pay": handshake_extract_pay,
    "handshake_extract_type": handshake_extract_type,
    "handshake_extract_duration": handshake_extract_duration,
    "handshake_extract_location": handshake_extract_location,
    "handshake_extract_deadline": handshake_extract_deadline
}


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


class TableGenerator(Shell):
    def __init__(self, table_schema_path: str, json_out_path: str, tsv_out_path: str):
        super().__init__(
            table_schema_path=table_schema_path,
            json_out_path=json_out_path,
            tsv_out_path=tsv_out_path
        )

    def _prompt_table_schema(self) -> dict:
        available_schemas = self._ls(self.table_schema_path, "*.json")
        if not available_schemas:
            print("Uh oh, no available schemas")
            return
        user_input = input(f"Please choose a schema {available_schemas}: ")
        while user_input not in available_schemas:
            print("Invalid selection")
            user_input = input(f"Please choose a schema {available_schemas}: ")
        path = self._get_table_schema_file_path(user_input)
        try:
            return self._load_json(path)
        except Exception as e:
            print(f"Json Load Error: {e}")
            return None

    def _prompt_json_out(self) -> [str]:
        available_folders = self._ls_dir(self.json_out_path)
        user_input = input(f"Please choose a folder {available_folders}: ")
        while user_input not in available_folders:
            print("Invalid selection")
            user_input = input(f"Please choose a folder {available_folders}: ")
        path = self._get_json_out_folder_path(user_input)
        files = []
        for name in self._ls(path):
            files.append(self._get_json_out_file_path(user_input, name))
        return files

    def _prompt_csv_out(self) -> str:
        user_input = input(f"Please enter a name for the output file: ")
        path = self._get_tsv_out_path(user_input)
        while self._is_path_taken(path):
            if input("Name is taken. Overwrite [y]? ") == "y":
                break
            user_input = input(f"Please enter a name for the output file: ")
            path = self._get_tsv_out_path(user_input)
        return path

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
        schema = self._prompt_table_schema()
        if not schema:
            return
        files = self._prompt_json_out()
        json_data = []
        for file in files:
            try:
               json_data.extend(self._load_json(file))
            except Exception as e:
                return print(f"Unexpected error: {e}")
        out_path = self._prompt_csv_out()
        self._generate_tsv(schema, json_data, out_path)