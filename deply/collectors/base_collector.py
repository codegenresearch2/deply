from abc import ABC, abstractmethod
from pathlib import Path
import ast

from ..models.code_element import CodeElement


class BaseCollector(ABC):
    @abstractmethod
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> set[CodeElement]:
        pass


class ClassInheritsCollector(BaseCollector):
    def __init__(self, base_class: str):
        self.base_class = base_class

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> set[CodeElement]:
        classes = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = get_base_name(base)
                    if base_name == self.base_class or base_name.endswith(f'.{self.base_class}'):
                        full_name = self._get_full_name(node)
                        code_element = CodeElement(file=file_path, name=full_name, element_type='class', line=node.lineno, column=node.col_offset)
                        classes.add(code_element)
        return classes

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return ''.join(reversed(names))