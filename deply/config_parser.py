from pathlib import Path
from typing import Any, Dict
import yaml


class ConfigParser:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def parse(self) -> Dict[str, Any]:
        with self.config_path.open("r") as f:
            config = yaml.safe_load(f)

        config = config.get('deply', config)
        config.setdefault('paths', [])
        config.setdefault('exclude_files', [])
        config.setdefault('layers', [])
        config.setdefault('ruleset', {})

        if not config['paths']:
            config['paths'] = [str(self.config_path.parent)]

        return config
