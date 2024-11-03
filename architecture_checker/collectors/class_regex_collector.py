import re
from pathlib import Path
from typing import Set
from .base_collector import BaseCollector
from ..utils.ast_utils import parse_file, get_classes_in_file


class ClassRegexCollector(BaseCollector):
    def __init__(self, config: dict, project_root: Path):
        self.regex = re.compile(config.get("regex", ""))
        self.project_root = project_root

    def collect(self) -> Set[Path]:
        collected_files = set()
        for file_path in self.project_root.rglob("*.py"):
            tree = parse_file(file_path)
            class_names = get_classes_in_file(tree)
            for class_name in class_names:
                if self.regex.match(class_name):
                    collected_files.add(file_path)
                    break
        return collected_files
