from src.file_processor import FileProcessor
from src.table_generator import TableGenerator

DATA_PATH = "./data"
WEB_SCHEMA_PATH = "./web_schemas"
JSON_OUT_PATH = "./json_out"
TABLE_SCHEMA_PATH = "./table_schemas"
TSV_OUT_PATH = "./tsv_out"


def main():
    GOODBYE = "Invalid input. Goodbye!"
    mode = input("Hello! Please select [1] extract json from html or [2] construct csv from json: ")
    try:
        mode = int(mode)
    except:
        return print(GOODBYE)
    
    match mode:
        case 1:
            program = FileProcessor(WEB_SCHEMA_PATH, DATA_PATH, JSON_OUT_PATH)
            program.interact()
        case 2:
            program = TableGenerator(TABLE_SCHEMA_PATH, JSON_OUT_PATH, TSV_OUT_PATH)
            program.interact()
        case _:
            return print(GOODBYE)
    return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")