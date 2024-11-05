from typing import Dict, Any
from pathlib import Path
from .base_collector import BaseCollector
from .file_regex_collector import FileRegexCollector
from .class_inherits_collector import ClassInheritsCollector


class CollectorFactory:
    @staticmethod
    def create(config: Dict[str, Any], project_root: Path) -> BaseCollector:
        collector_type = config.get("type")
        if collector_type == "file_regex":
            return FileRegexCollector(config, project_root)
        elif collector_type == "class_inherits":
            return ClassInheritsCollector(config, project_root)
        else:
            raise ValueError(f"Unknown collector type: {collector_type}")
