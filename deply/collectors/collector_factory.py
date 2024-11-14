from typing import Dict, Any

from .base_collector import BaseCollector
from .class_inherits_collector import ClassInheritsCollector
from .file_regex_collector import FileRegexCollector


class CollectorFactory:
    @staticmethod
    def create(config: Dict[str, Any], paths: list[str], exclude_file: list[str]) -> BaseCollector:
        collector_type = config.get("type")
        if collector_type == "file_regex":
            return FileRegexCollector(config, paths, exclude_file)
        elif collector_type == "class_inherits":
            return ClassInheritsCollector(config, paths, exclude_file)
        else:
            raise ValueError(f"Unknown collector type: {collector_type}")
