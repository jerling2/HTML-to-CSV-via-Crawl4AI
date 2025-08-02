"""
This mode should define how the python main application functions.
"""
from src.interface import UserMode


class SystemMode(UserMode):
    def __init__(self, base_paths):
        super().__init__(base_paths)
    
    def interact(self):
        print("works!")