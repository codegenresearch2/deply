from typing import Dict, Any, List
from .base_collector import BaseCollector
from .class_inherits_collector import ClassInheritsCollector
from .class_name_regex_collector import ClassNameRegexCollector
from .directory_collector import DirectoryCollector
from .file_regex_collector import FileRegexCollector
from .decorator_usage_collector import DecoratorUsageCollector
from .bool_collector import BoolCollector
from .function_name_regex_collector import FunctionNameRegexCollector

class CollectorFactory:
    @staticmethod
    def create(config: Dict[str, Any], paths: List[str], exclude_files: List[str]) -> BaseCollector:
        collector_type = config.get("type")
        if collector_type == "file_regex":
            return FileRegexCollector(config, paths, exclude_files)
        elif collector_type == "class_inherits":
            return ClassInheritsCollector(config)
        elif collector_type == "class_name_regex":
            return ClassNameRegexCollector(config, paths, exclude_files)
        elif collector_type == "function_name_regex":
            return FunctionNameRegexCollector(config)
        elif collector_type == "directory":
            return DirectoryCollector(config, paths, exclude_files)
        elif collector_type == "decorator_usage":
            return DecoratorUsageCollector(config)
        elif collector_type == "bool":
            return BoolCollector(config, paths, exclude_files)
        else:
            raise ValueError(f"Unknown collector type: {collector_type}")