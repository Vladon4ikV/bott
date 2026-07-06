import json
import os

FILE = "cache.json"

def load_cache():
    return json.load(open(FILE)) if os.path.exists(FILE) else {}

def save_cache(data):
    json.dump(data, open(FILE, "w"), indent=2)