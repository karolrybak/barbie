#!./.venv/bin/python3.11

#! Refactor
import importlib
import json
import os
from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler
import configparser

CONFIG_FILE = "barbie.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

client = OpenAI()

class EventHandler(AssistantEventHandler):    
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)
        
    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    @override
    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)

    def handle_requires_action(self, data, run_id):
        tool_outputs = []

        for tool in data.required_action.submit_tool_outputs.tool_calls:
            function_name = tool.function.name
            function_path = f"tools/{function_name}.py"

            print("checking  " + function_path)
            
            if os.path.isfile(function_path):
                print("found tool")
                module_name = f"tools.{function_name}"
                module = importlib.import_module(module_name)
                function = getattr(module, function_name)
                output = function()
                print("got result: " + output)
            else:
                output = None

            tool_outputs.append({"tool_call_id": tool.id, "output": output})
            self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(),
        ) as stream:
            for text in stream.text_deltas:
                print(text, end="", flush=True)
        print()

def init_platform():
    if config["thread"]["id"]:
        thread = client.beta.threads.retrieve(config["thread"]["id"])
    if not thread:
        thread = client.beta.threads.create()
        config["thread"]["id"] = thread.id
        config.write(open(CONFIG_FILE, 'w'))
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="List projects"
        )
    return thread
    
thread = init_platform()

assistant = client.beta.assistants.retrieve(config["assistant"]["id"])

with client.beta.threads.runs.stream(
  thread_id=thread.id,
  assistant_id=assistant.id,
  event_handler=EventHandler(),
) as stream:
  stream.until_done()