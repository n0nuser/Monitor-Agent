import os
import sys
import json
from monitor_agent.core.helper import save2log


rel_path = "settings.json"
dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
abs_file_path = os.path.join(dir, rel_path)


class Settings:
    def __init__(self):
        self.as_dict: dict = self._read_settings_file()
        obj = toObj(self.as_dict)
        self.alerts = obj.alerts
        self.metrics = obj.metrics
        self.thresholds = obj.thresholds
        self.uvicorn = obj.uvicorn

    def _read_settings_file(self):
        try:
            f = open(abs_file_path, "r")
            data = f.read()
            data_dict = json.loads(data)
            data_str, data_dict = _write_file(data_dict, abs_file_path)
        except (json.JSONDecodeError, ValueError, FileNotFoundError) as msg:
            print(f"ERROR: Invalid JSON settings file - {msg}", file=sys.stderr)
            save2log(type="ERROR", data=f"Invalid JSON file - {msg}")
            exit()

        return data_dict

    def write_settings(self, data: str):
        try:
            data_dict = json.loads(data)
            data_str, data_dict = _write_file(data_dict, abs_file_path)
        except (json.JSONDecodeError, ValueError) as msg:
            return {"status": f"Error: {msg}", "data": data}

        self.settings = data_dict
        return {"status": "success", "data": data_dict}


######################
## Helper functions ##
######################


def toObj(item):
    """Jakub Dóka: https://stackoverflow.com/a/65969444"""
    if isinstance(item, dict):
        obj = type("__object", (object,), {})

        for key, value in item.items():
            setattr(obj, key, toObj(value))

        return obj
    elif isinstance(item, list):
        return map(toObj, item)
    else:
        return item


def _write_file(data: dict, path: str):
    f = open(path, "w")
    data_str: str = json.dumps(data, indent=4, sort_keys=True)
    f.write(data_str)
    return data_str, data
