import importlib

class ToolRunner:
    """ It will run task """
    def __init__(self) -> None:
        return

    def run(self, cmd: str, args):
        """ asd """
        module_name = "tools." + cmd.split("_")[0]
        function_name = cmd.split("_")[0]
        module = importlib.import_module(module_name) 
        function = getattr(module, function_name)
        output = function(args)
        
        return output
        
    
class BaseTool:
    """ Base class for all tools """
    tool_name = None
    