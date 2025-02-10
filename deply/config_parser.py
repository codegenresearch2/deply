from pathlib import Path
from typing import Any, Dict
import yaml

class ConfigParser:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def parse(self) -> Dict[str, Any]:
        with self.config_path.open("r") as f:
            config = yaml.safe_load(f)

        # Ensure the necessary keys are present in the config
        deply_config = config.get('deply', {})
        paths = deply_config.get('paths', [])
        exclude_files = deply_config.get('exclude_files', [])
        layers = deply_config.get('layers', [])
        ruleset = deply_config.get('ruleset', {})

        # Return the parsed configuration
        return {
            'paths': paths,
            'exclude_files': exclude_files,
            'layers': layers,
            'ruleset': ruleset
        }