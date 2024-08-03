import torch
from TTS.api import TTS
from barbie.tools.base import BaseTool, Singleton

class tts(BaseTool, Singleton):
    tts_instance = None
    
    def __init__(self) -> None:
        print("Seting up")
        # Get device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print("Running on " + device)
        self.tts_instance = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        return
    
    def say(self, voice, text):
        result = self.tts_instance.tts()