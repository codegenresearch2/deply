from pathlib import Path
from typing import Set
from .base_collector import BaseCollector
from ..utils.ast_utils import parse_file, get_classes_in_file


class ClassNameCollector(BaseCollector):
    def __init__(self, config: dict, project_root: Path):
        self.class_name = config.get("name", "")
        self.project_root = project_root

    def collect(self) -> Set[Path]:
        collected_files = set()
        for file_path in self.project_root.rglob("*.py"):
            tree = parse_file(file_path)
            class_names = get_classes_in_file(tree)
            if self.class_name in class_names:
                collected_files.add(file_path)
        return collected_files
