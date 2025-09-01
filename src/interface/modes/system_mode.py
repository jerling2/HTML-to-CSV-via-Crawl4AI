from src.interface import (
    UserMode, 
    LocalExtractMode,
    ConvertJsonToTSVMode,
    RemoteHandshake,
    RemoteHandshakeSummary,
    DatabaseMode,
)

class SystemMode(UserMode):
    def __init__(self, base_paths):
        super().__init__(base_paths)
    
    def interact(self):
        GOODBYE = "Invalid input. Goodbye!"
        mode = input("  [1] 'Local Extract'\n  [2] 'Json to TSV'\n  [3] 'Remote Handshake'\n  [4] 'Remote Handshake Content'\n  [5] 'Database'\nHello! Please select a mode: ")
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
            case 4:
                program = RemoteHandshakeSummary()
                program.interact()
            case 5:
                program = DatabaseMode()
                program.interact()
            case _:
                return print(GOODBYE)
        return