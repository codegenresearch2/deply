import ast
import re
from pathlib import Path
from typing import List, Set

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement

class DecoratorUsageCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.decorator_name = config.get('decorator_name', '')
        self.decorator_regex_pattern = config.get('decorator_regex', '')
        self.exclude_files_regex_pattern = config.get('exclude_files_regex', '')
        self.decorator_regex = re.compile(self.decorator_regex_pattern) if self.decorator_regex_pattern else None
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        for base_path in self.paths:
            if base_path.exists():
                files = [f for f in base_path.rglob('*.py') if f.is_file()]
                for file_path in files:
                    if not self._is_excluded(file_path, base_path):
                        tree = self._parse_file(file_path)
                        if tree is not None:
                            elements = self.match_in_file(tree, file_path)
                            collected_elements.update(elements)
        return collected_elements

    def _is_excluded(self, file_path: Path, base_path: Path) -> bool:
        relative_path = str(file_path.relative_to(base_path))
        return any(pattern.search(relative_path) for pattern in self.exclude_files) or (self.exclude_regex and self.exclude_regex.match(relative_path))

    def _parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def match_in_file(self, tree, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    decorator_name = self._get_decorator_name(decorator)
                    if (self.decorator_name and decorator_name == self.decorator_name) or (self.decorator_regex and self.decorator_regex.match(decorator_name)):
                        full_name = self._get_full_name(node)
                        element_type = 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class'
                        elements.add(CodeElement(file=file_path, name=full_name, element_type=element_type, line=node.lineno, column=node.col_offset))
        return elements

    def _get_decorator_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_decorator_name(node.value)
            return f'{value}.{node.attr}' if value else node.attr
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        else:
            return ''

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))