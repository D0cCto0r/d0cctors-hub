import json
import os
import sys


def resource_path(relative_path):
    """ Soporte PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ConfigManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(base_dir, "config.json")
        self.default_config = {
            "minecraft_path": "",
            "steam_path": "",
            "installed_servers": {
                "Minecraft": False,
                "Ark Survival": False
            },
            "ram_allocation": 4096
        }

        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            self.save_config(self.default_config)
            return self.default_config.copy()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validación estructural mínima
            if not isinstance(data, dict):
                raise ValueError("Config inválida")

            if "installed_servers" not in data:
                data["installed_servers"] = {}

            return data

        except Exception as e:
            print("Config corrupta, recreando archivo...")
            self.save_config(self.default_config)
            return self.default_config.copy()

    def save_config(self, config_data=None):
        if config_data is not None:
            self.config = config_data

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def set_installed(self, server_name, value):
        if "installed_servers" not in self.config:
            self.config["installed_servers"] = {}

        self.config["installed_servers"][server_name] = value
        self.save_config()