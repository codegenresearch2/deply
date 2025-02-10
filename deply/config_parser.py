from pathlib import Path
from typing import Any, Dict
import yaml


class ConfigParser:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def parse(self) -> Dict[str, Any]:
        with self.config_path.open("r") as f:
            config = yaml.safe_load(f)

        deply_config = config.get('deply', {})
        deply_config.setdefault('paths', [])
        deply_config.setdefault('exclude_files', [])
        deply_config.setdefault('layers', [])
        deply_config.setdefault('ruleset', {})

        return deply_config