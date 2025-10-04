import json

def load_schema():
    with open("memory_schema.json") as f:
        return json.load(f)
