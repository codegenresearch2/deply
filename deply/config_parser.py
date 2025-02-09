from pathlib import Path\\\\\nfrom typing import Any, Dict\\nimport yaml\\n\\nclass ConfigParser:\\\\\\n    def __init__(self, config_path: Path):\\n        self.config_path = config_path\\n\\n    def parse(self) -> Dict[str, Any]:\\n        with self.config_path.open("r") as f:\\n            config = yaml.safe_load(f)\\\\\n\\n        config = config.get('deply', config)\\\\\\\n        config.setdefault('paths', [] if 'paths' not in config else [str(self.config_path.parent)])\\\\\\\\n        config.setdefault('exclude_files', [])\\\\\\\\n        config.setdefault('layers', [])\\\\\\\\n        config.setdefault('ruleset', {})\\\\\\\\n\\n        return config