#!./.venv/bin/python3.11
import configparser
import json
from typing_extensions import override
from openai import OpenAI
from openai import AssistantEventHandler
import sys
import time
import subprocess
from openai.types.beta.threads import Text

CONFIG_FILE = "barbie.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

last_selection = None

client = OpenAI()
thread = client.beta.threads.create()
ai_active = False
last_responses = []
#! Encapsulate into static class

def set_clipboard(text, selection="clipboard"):
    process = subprocess.Popen(['xclip', '-selection', selection], stdin=subprocess.PIPE)
    process.communicate(input=text.encode('utf-8'))

def get_clipboard(selection="clipboard"):
    process = subprocess.Popen(['xclip', '-selection', selection, '-o'], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    return output.decode('utf-8')

def get_window_info():
    window = {}

    process = subprocess.Popen(['xdotool', 'getactivewindow'], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    window["id"] =  output.decode('utf-8')

    process = subprocess.Popen(['xdotool', 'getwindowname', window["id"]], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    window["name"] = output

    process = subprocess.Popen(['xdotool', 'getwindowclassname', window["id"]], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    window["classname"] = output
    return window


#! create clipboardService class and move all related code there+


class EventHandler(AssistantEventHandler):    
    @override
    def on_text_created(self, text: Text) -> None:
        print("AI RESPONSE")
        
        print("DUMPS")
        print(json.dumps(text.value))
        print("/DUMPS")

        set_clipboard(text.value, selection="clipboard")
        global last_selection
        last_selection = None
        global window_info        
        print(window_info)
        print(text.value, end="", flush=True)
        global ai_active
        ai_active = False

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

def handle_clipboard_change(text:str):
    global ai_active 
    print("Clipboard changed to " + text)
    print(window_info)
    
    if str(window_info["classname"]).find("Element"):
        assistant = client.beta.assistants.retrieve(config["reishi"]["id"])
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Napisz w stylu króla Juliana nie dodawaj za dużo tekstu:" +text
        )
        print("run job")
    
        global ai_active 
        ai_active = True
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            event_handler=EventHandler(),
        ) as stream:
            stream.until_done()
        return
    if not "#! " in text:
        print("No command exiting")
        return
    
    print("---- RUNNING AI !!!")
    
    assistant = client.beta.assistants.retrieve(config["reishi"]["id"])
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=text
    )
    
    print("run job")   
    ai_active = True
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()
        
def clipboard_monitor():
    global last_selection
    new_selection = get_clipboard(selection="clipboard")
    if last_selection != new_selection:
        if last_selection is not None:
            global window_info
            window_info = get_window_info()
            last_selection = new_selection
            handle_clipboard_change(last_selection)
        last_selection = new_selection
        

def main_loop():
    while 1:
        if not ai_active:
            clipboard_monitor()
        time.sleep(0.1)

if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        # print >> sys.stderr, '\nExiting by user request.\n'
        sys.exit(0)