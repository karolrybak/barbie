import json
import re

STATE_FILE = "state.json"

def project_create(name):
    with open(STATE_FILE, "a+") as f:
        state = json.load(f)
        
        unique_id = re.sub(r'\W+', '', name)
        #! try adding _1 _2 to id until it's unique
        project = {
            "name": name,
            "id": unique_id
        }
        state["projects"].append(project)
                
        f.seek(0)
        f.truncate()
        json.dump(state, f)
        f.close()