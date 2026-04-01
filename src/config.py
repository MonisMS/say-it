import json
import os

DEFAULTS = {
    "model": "medium",
    "language": "auto",
    "task": "transcribe",   # "transcribe" or "translate" (translate → always English output)
    "hotkey": "right alt",
    "sample_rate": 16000,
    "device": None,
}


class Config:
    def __init__(self):
        config_dir = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")), "say-it"
        )
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "config.json")

        if os.path.exists(config_path):
            with open(config_path) as f:
                data = json.load(f)
        else:
            data = {}
            with open(config_path, "w") as f:
                json.dump(DEFAULTS, f, indent=2)
            print(f"Config created at {config_path}")

        merged = {**DEFAULTS, **data}
        for key, value in merged.items():
            setattr(self, key, value)
