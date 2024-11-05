import ast
from pathlib import Path
from typing import Set
from .base_collector import BaseCollector
from ..models.code_element import CodeElement
from ..utils.ast_utils import get_import_aliases, get_base_name


class ClassInheritsCollector(BaseCollector):
    def __init__(self, config: dict, project_root: Path):
        self.base_class = config.get("base_class", "")
        self.project_root = project_root

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        for file_path in self.project_root.rglob("*.py"):
            tree = self.parse_file(file_path)
            classes = self.get_classes_inheriting(tree, file_path)
            collected_elements.update(classes)

        return collected_elements

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except SyntaxError:
            return None

    def get_classes_inheriting(self, tree, file_path: Path) -> set[CodeElement]:
        import_aliases = get_import_aliases(tree)
        classes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = get_base_name(base, import_aliases)
                    if base_name == self.base_class:
                        code_element = CodeElement(
                            file=file_path,
                            name=node.name,
                            element_type='class'
                        )
                        classes.add(code_element)
        return classes
