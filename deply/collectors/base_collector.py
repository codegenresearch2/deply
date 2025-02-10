import ast
from pathlib import Path
from typing import Set
from ..models.code_element import CodeElement
from abc import ABC, abstractmethod

class BaseCollector(ABC):
    @abstractmethod
    def collect(self) -> Set[CodeElement]:
        pass

class ClassInheritsCollector(BaseCollector):
    def __init__(self, config: dict, paths: list[str], exclude_files: list[str]):
        self.base_class = config.get("base_class", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> set[CodeElement]:
        if self.exclude_regex:
            if self.exclude_regex.search(str(file_path)):
                return set()
        import_aliases = get_import_aliases(file_ast)
        classes = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = get_base_name(base, import_aliases)
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
        return ".".join(reversed(names))