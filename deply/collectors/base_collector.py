from abc import ABC, abstractmethod
from typing import Set
from pathlib import Path
import ast

from ..models.code_element import CodeElement


class BaseCollector(ABC):
    @abstractmethod
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        pass


class ClassInheritsCollector(BaseCollector):
    def __init__(self, config: dict, paths: list[str], exclude_files: list[str]):
        self.config = config
        self.paths = paths
        self.exclude_files = exclude_files
        self.base_class = config.get("base_class", "")
        self.exclude_regex = re.compile(config.get("exclude_files_regex", "")) if config.get("exclude_files_regex", "") else None

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> set[CodeElement]:
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return set()
        classes = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = get_base_name(base)
                    if base_name == self.base_class or base_name.endswith(f".{self.base_class}"):
                        full_name = self._get_full_name(node)
                        code_element = CodeElement(file=file_path, name=full_name, element_type="class", line=node.lineno, column=node.col_offset)
                        classes.add(code_element)
        return classes

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, "parent", None)
        return "".join(reversed(names))