import ast
import re
from pathlib import Path
from typing import List, Set

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement

class DecoratorUsageCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.decorator_name = config.get("decorator_name", "")
        self.decorator_regex_pattern = config.get("decorator_regex", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.decorator_regex = re.compile(self.decorator_regex_pattern) if self.decorator_regex_pattern else None
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return set()

        # self.annotate_parent(file_ast)
        elements = set()
        for node in ast.walk(file_ast):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    d_name = self._get_decorator_name(decorator)
                    if (self.decorator_name and d_name == self.decorator_name) or (self.decorator_regex and self.decorator_regex.match(d_name)):
                        full_name = self._get_full_name(node)
                        element_type = "function" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "class"
                        elements.add(CodeElement(file=file_path, name=full_name, element_type=element_type, line=node.lineno, column=node.col_offset))
        return elements

    def _get_decorator_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_decorator_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        else:
            return ""

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(current.name)
            current = getattr(current, "parent", None)
        return ".".join(reversed(names))

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node