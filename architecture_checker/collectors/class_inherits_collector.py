from pathlib import Path
from typing import Set
from .base_collector import BaseCollector
from ..utils.ast_utils import parse_file, get_classes_inheriting
from ..models.code_element import CodeElement


class ClassInheritsCollector(BaseCollector):
    def __init__(self, config: dict, project_root: Path):
        self.base_class = config.get("base_class", "")
        self.project_root = project_root

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        for file_path in self.project_root.rglob("*/models.py"):
            tree = parse_file(file_path)
            classes = get_classes_inheriting(tree, self.base_class, file_path, self.project_root)

            collected_elements.update(classes)

        return collected_elements
