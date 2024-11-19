from typing import Dict, Any

from . import DecoratorUsageCollector
from .base_collector import BaseCollector
from .class_inherits_collector import ClassInheritsCollector
from .class_name_regex_collector import ClassNameRegexCollector
from .directory_collector import DirectoryCollector
from .file_regex_collector import FileRegexCollector


class CollectorFactory:
    @staticmethod
    def create(config: Dict[str, Any], paths: list[str], exclude_files: list[str]) -> BaseCollector:
        collector_type = config.get("type")
        if collector_type == "file_regex":
            return FileRegexCollector(config, paths, exclude_files)
        elif collector_type == "class_inherits":
            return ClassInheritsCollector(config, paths, exclude_files)
        elif collector_type == "class_name_regex":
            return ClassNameRegexCollector(config, paths, exclude_files)
        elif collector_type == "directory":
            return DirectoryCollector(config, paths, exclude_files)
        elif collector_type == "decorator_usage":
            return DecoratorUsageCollector(config, paths, exclude_files)
        elif collector_type == "bool":
            from .bool_collector import BoolCollector
            return BoolCollector(config, paths, exclude_files)
        else:
            raise ValueError(f"Unknown collector type: {collector_type}")
