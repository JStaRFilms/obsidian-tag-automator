import os
import json
from pathlib import Path

class ConfigManager:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.config_path = self.vault_path / "automator_config.json"
        self.config = self._load_config()

    def _load_config(self):
        """Load the automator configuration from `automator_config.json`."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    # Ensure exclusion lists are sets for efficient lookup
                    config_data['excluded_tags'] = list(set(config_data.get('excluded_tags', [])))
                    config_data['excluded_paths'] = list(set(config_data.get('excluded_paths', [])))
                    return config_data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}. Using default configuration.")
        
        return {'excluded_tags': [], 'excluded_paths': []}  # Initialize with empty lists if no config

    def save_config(self):
        """Save the current automator configuration to `automator_config.json`."""
        # Ensure excluded_tags and excluded_paths are saved as lists
        self.config['excluded_tags'] = list(self.config.get('excluded_tags', []))
        self.config['excluded_paths'] = list(self.config.get('excluded_paths', []))
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_path}")
        except IOError as e:
            print(f"Error saving config file: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()