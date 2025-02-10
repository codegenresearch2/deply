from typing import Dict, Any

from .base_collector import BaseCollector
from .collectors import (
    FileRegexCollector,
    ClassInheritsCollector,
    ClassNameRegexCollector,
    DirectoryCollector,
    DecoratorUsageCollector
)

class CollectorFactory:
    COLLECTORS = {
        "file_regex": FileRegexCollector,
        "class_inherits": ClassInheritsCollector,
        "class_name_regex": ClassNameRegexCollector,
        "directory": DirectoryCollector,
        "decorator_usage": DecoratorUsageCollector,
        "bool": "BoolCollector"
    }

    @classmethod
    def create(cls, config: Dict[str, Any], paths: list[str], exclude_files: list[str]) -> BaseCollector:
        collector_type = config.get("type")
        collector_class = cls.COLLECTORS.get(collector_type)

        if collector_class is None:
            raise ValueError(f"Unknown collector type: {collector_type}")

        if collector_type == "bool":
            from .bool_collector import BoolCollector
            collector_class = BoolCollector

        return collector_class(config, paths, exclude_files)


In the rewritten code, I have:

1. Imported the collectors directly from the `collectors` module to improve code readability and maintainability.
2. Created a `COLLECTORS` dictionary to map collector types to their corresponding classes. This reduces redundant operations in the `create` method.
3. Used the `classmethod` decorator for the `create` method to allow it to be called on the class itself, rather than on an instance of the class. This makes the method more flexible and reusable.
4. Moved the import statement for the `BoolCollector` inside the `create` method to avoid unnecessary imports when the `BoolCollector` is not needed.
5. Raised a `ValueError` if the collector type is unknown, which improves error handling and makes the code more robust.