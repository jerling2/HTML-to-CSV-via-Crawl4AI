from src.interface import UserMode, LocalExtractMode, ConvertJsonToTSVMode, RemoteHandshake


class SystemMode(UserMode):
    def __init__(self, base_paths):
        super().__init__(base_paths)
    
    def interact(self):
        GOODBYE = "Invalid input. Goodbye!"
        mode = input("Hello! Please select: [1] 'Local Extract', [2] 'Json to TSV', or [3] 'Remote Handshake': ")
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
                program = RemoteHandshake()
                program.interact()
            case _:
                return print(GOODBYE)
        return