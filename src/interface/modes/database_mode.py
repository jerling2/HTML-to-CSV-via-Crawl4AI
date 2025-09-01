import json
from ..abstracts.user_mode import UserMode
from src.systems import VectorDatabase


class DatabaseMode(UserMode):

    def __init__(self):
        super().__init__()

    def interact(self):

        INVALID_INPUT = "Invalid input."
        WELCOME_MSG = "\x1b[1;36mWelcome to the Database Terminal!\x1b[0;36m (^C to Quit)\x1b[0m"
        ERROR_NO_AVAILABLE_COLLECTIONS = "\x1b[1mError: No available collections\x1b[0m\n" + WELCOME_MSG
        print(WELCOME_MSG)
        while (mode := input("\x1b[93m  [1] 'Create Collection'\n  [2] 'List Collections'\n  [3] 'Describe Collection'\n  [4] 'Drop Collection'\n  [5] 'LIMIT Query a Collection'\x1b[0m\n[Database Mode] Please choose an option: ")):
            try:
                mode = int(mode)
            except:
                print(INVALID_INPUT)
                continue
            match mode:
                case 1:
                    config_path = self.prompt_choose('schema_table', "Please choose a table schema")
                    collection_name = self.prompt_enter('milvus', "Please enter a name for new collection")
                    self.db.create_collection(collection_name, config_path)
                case 2:
                    available = self.db.list_collections()
                    if not available:
                        print(ERROR_NO_AVAILABLE_COLLECTIONS)
                        continue
                    print("\x1b[1mAvailable collections:\x1b[0m")
                    for collection in available:
                        print(f'\x1b[1m  - "{collection}"\x1b[0m')
                case 3:
                    collection_name = self.prompt_choose('milvus', "Please choose a collection")
                    if collection_name is None:
                        print(ERROR_NO_AVAILABLE_COLLECTIONS)
                        continue
                    res = self.db.describe_collection(collection_name)
                    print(json.dumps(res, indent=2))
                case 4:
                    collection_name = self.prompt_choose('milvus', "Please choose a collection")
                    if collection_name is None:
                        print(ERROR_NO_AVAILABLE_COLLECTIONS)
                        continue
                    self.db.drop_collection(collection_name)
                case 5:
                    collection_name = self.prompt_choose('milvus', "Please choose a collection")
                    if collection_name is None:
                        print(ERROR_NO_AVAILABLE_COLLECTIONS)
                        continue
                    while True:
                        try:
                            limit = int(input("Enter a limit: "))
                            if limit > 0:
                                break
                            print("Error: out of range.")
                        except:
                            print("invalid input.")
                    self.db.load_collection(collection_name)
                    res = self.db.query(
                        collection_name,
                        limit=limit,
                        output_fields=["*"]
                    )
                    self.db.release_collection(collection_name)
                    print(res)
                case _:
                    print(INVALID_INPUT)
            print(WELCOME_MSG)
        return

        