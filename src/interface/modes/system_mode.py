from src.interface import UserMode, LocalExtractMode, ConvertJsonToTSVMode, DevMode


class SystemMode(UserMode):
    def __init__(self, base_paths):
        super().__init__(base_paths)
    
    def interact(self):
        GOODBYE = "Invalid input. Goodbye!"
        mode = input("Hello! Please select [1] extract json from html or [2] construct tsv from json: ")
        try:
            mode = int(mode)
        except:
            return print(GOODBYE)
        match mode:
            case 1:
                program = LocalExtractMode()
                program.interact()
            case 2:
                program = ConvertJsonToTSVMode()
                program.interact()
            case 3:
                print('running dev mode')
                program = DevMode()
                program.interact()
            case _:
                return print(GOODBYE)
        return