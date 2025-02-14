import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_base_name, get_import_aliases

class DecoratorUsageCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.decorator_name = config.get("decorator_name", "")
        self.decorator_regex_pattern = config.get("decorator_regex", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.decorator_regex = re.compile(self.decorator_regex_pattern) if self.decorator_regex_pattern else None
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        all_files = self.get_all_files()

        for file_path in all_files:
            tree = self.parse_file(file_path)
            if tree is None:
                continue
            self.annotate_parent(tree)
            import_aliases = get_import_aliases(tree)
            elements = self.get_elements_with_decorator(tree, file_path, import_aliases)
            collected_elements.update(elements)

        return collected_elements

    def get_all_files(self) -> List[Path]:
        all_files = []

        for base_path in self.paths:
            if base_path.exists():
                files = list(base_path.rglob('*.py'))
                files = [f for f in files if f.is_file() and not self.is_excluded(f)]
                all_files.extend(files)

        return all_files

    def is_excluded(self, file_path: Path) -> bool:
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return True
        for pattern in self.exclude_files:
            if pattern.search(str(file_path)):
                return True
        return False

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def get_elements_with_decorator(self, tree, file_path: Path, import_aliases: dict) -> Set[CodeElement]:
        elements = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    decorator_name = self._get_full_name(decorator, import_aliases)
                    if self.decorator_name and decorator_name == self.decorator_name:
                        full_name = self._get_full_name(node, import_aliases)
                        code_element = self.create_code_element(file_path, full_name, node)
                        elements.add(code_element)
                    elif self.decorator_regex and self.decorator_regex.match(decorator_name):
                        full_name = self._get_full_name(node, import_aliases)
                        code_element = self.create_code_element(file_path, full_name, node)
                        elements.add(code_element)
        return elements

    def create_code_element(self, file_path: Path, full_name: str, node: ast.AST) -> CodeElement:
        element_type = 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class'
        return CodeElement(file=file_path, name=full_name, element_type=element_type, line=node.lineno, column=node.col_offset)

    def _get_full_name(self, node, import_aliases: dict):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_full_name(node.value, import_aliases)
            return f"{value}.{node.attr}"
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names = []
            current = node
            while isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(current.name)
                current = getattr(current, 'parent', None)
            return '.'.join(reversed(names))
        elif isinstance(node, ast.Call):
            return self._get_full_name(node.func, import_aliases)
        elif isinstance(node, ast.Subscript):
            base_name = get_base_name(node.value, import_aliases)
            slice_value = self._get_full_name(node.slice.value, import_aliases)
            return f"{base_name}[{slice_value}]"
        else:
            return ''

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node

The provided code snippet has been rewritten according to the rules provided. The main changes include:

1. The `get_all_files` method has been simplified to collect all files in the specified paths that are not excluded by either the global exclude patterns or the collector-specific exclude pattern.
2. The `is_excluded` method has been added to check if a file is excluded based on the global exclude patterns and the collector-specific exclude pattern.
3. The `get_elements_with_decorator` method now takes an additional `import_aliases` argument, which is used to resolve the full name of the decorator.
4. The `create_code_element` method has been added to create a `CodeElement` object with the file path, full name, element type, line number, and column offset.
5. The `_get_full_name` method has been updated to handle `ast.Subscript` nodes, which are used to denote array indexing or slicing.

These changes enhance code organization and clarity, improve file collection and exclusion logic, and utilize AST for code analysis efficiently.