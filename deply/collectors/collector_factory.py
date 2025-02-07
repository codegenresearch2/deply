from typing import Dict, Any\\nfrom . import DecoratorUsageCollector\\nfrom .base_collector import BaseCollector\\nfrom .class_inherits_collector import ClassInheritsCollector\\nfrom .class_name_regex_collector import ClassNameRegexCollector\\nfrom .directory_collector import DirectoryCollector\\nfrom .file_regex_collector import FileRegexCollector\\n\\nclass CollectorFactory:\\n    @staticmethod\\n    def create(config: Dict[str, Any], paths: list[str], exclude_files: list[str]) -> BaseCollector:\\n            collector_type = config.get('type')\\n            if collector_type == 'file_regex':\\n                return FileRegexCollector(config, paths, exclude_files)\\n            elif collector_type == 'class_inherits':\\n                return ClassInheritsCollector(config, paths, exclude_files)\\n            elif collector_type == 'class_name_regex':\\n                return ClassNameRegexCollector(config, paths, exclude_files)\\n            elif collector_type == 'directory':\\n                return DirectoryCollector(config, paths, exclude_files)\\n            elif collector_type == 'decorator_usage':\\n                return DecoratorUsageCollector(config, paths, exclude_files)\\n            elif collector_type == 'bool':\\n                from .bool_collector import BoolCollector\\n                return BoolCollector(config, paths, exclude_files)\\n            else:\\n                raise ValueError(f'Unknown collector type: {collector_type}')