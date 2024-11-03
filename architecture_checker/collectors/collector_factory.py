from typing import Dict, Any
from pathlib import Path
from .base_collector import BaseCollector
from .file_regex_collector import FileRegexCollector
from .path_collector import PathCollector
from .module_collector import ModuleCollector
from .filename_collector import FilenameCollector
from .class_name_collector import ClassNameCollector
from .class_regex_collector import ClassRegexCollector
from .class_inherits_collector import ClassInheritsCollector
from .namespace_collector import NamespaceCollector
from .ext_collector import ExtCollector
from .tag_collector import TagCollector


class CollectorFactory:
    @staticmethod
    def create(config: Dict[str, Any], project_root: Path) -> BaseCollector:
        collector_type = config.get("type")
        if collector_type == "file_regex":
            return FileRegexCollector(config, project_root)
        elif collector_type == "path":
            return PathCollector(config, project_root)
        elif collector_type == "module":
            return ModuleCollector(config, project_root)
        elif collector_type == "filename":
            return FilenameCollector(config, project_root)
        elif collector_type == "class_name":
            return ClassNameCollector(config, project_root)
        elif collector_type == "class_regex":
            return ClassRegexCollector(config, project_root)
        elif collector_type == "class_inherits":
            return ClassInheritsCollector(config, project_root)
        elif collector_type == "namespace":
            return NamespaceCollector(config, project_root)
        elif collector_type == "ext":
            return ExtCollector(config, project_root)
        elif collector_type == "tag":
            return TagCollector(config, project_root)
        else:
            raise ValueError(f"Unknown collector type: {collector_type}")
