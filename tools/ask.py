import pyautogui
from barbie.tools.base import BaseTool

class AskTool(BaseTool):
    tool_name = "ask"
    def yesno(prompt):
        return pyautogui.confirm(prompt) == "OK"
    def promptText(prompt):
        return pyautogui.prompt(prompt)