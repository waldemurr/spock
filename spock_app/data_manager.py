import json
import os


class DataManager:
    def __init__(self, filename="data/trades.json"):
        self.filename = filename
        os.makedirs(os.path.dirname(filename), exist_ok=True)

    def load_data(self):
        try:
            with open(self.filename, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"trades": [], "currencies": {}}

    def save_data(self, data):
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=2)
