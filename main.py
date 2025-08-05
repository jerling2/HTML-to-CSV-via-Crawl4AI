from dotenv import load_dotenv
from src.interface import SystemMode


load_dotenv()


if __name__ == "__main__":
    main = SystemMode({
        'schema_html': './configs/html_schemas',
        'schema_table': './configs/table_schemas',
        'data_content': './data/content',
        'data_html': './data/html',
        'data_table': './data/table'
    })
    try:
        main.interact()
    except KeyboardInterrupt:
        print("\nGoodbye!")