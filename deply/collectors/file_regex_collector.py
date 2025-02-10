import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement

class FileRegexCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.regex_pattern = config.get("regex", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.element_type = config.get("element_type", "")  # 'class', 'function', 'variable'

        self.regex = re.compile(self.regex_pattern)
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def match_in_file(self, file_path: Path, base_path: Path) -> Set[CodeElement]:
        # Apply exclude patterns
        if self.is_excluded(file_path, base_path):
            return set()

        elements = set()
        tree = self.parse_file(file_path)
        if tree is None:
            return elements

        if not self.element_type or self.element_type == 'class':
            elements.update(self._collect_class_names(tree, file_path))

        if not self.element_type or self.element_type == 'function':
            elements.update(self._collect_function_names(tree, file_path))

        if not self.element_type or self.element_type == 'variable':
            elements.update(self._collect_variable_names(tree, file_path))

        return elements

    def is_excluded(self, file_path: Path, base_path: Path) -> bool:
        relative_path = str(file_path.relative_to(base_path))
        return any(pattern.search(relative_path) for pattern in self.exclude_files) or (self.exclude_regex and self.exclude_regex.match(relative_path))

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def _collect_class_names(self, tree, file_path: Path) -> Set[CodeElement]:
        classes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                full_name = self._get_full_name(node)
                code_element = CodeElement(
                    file=file_path,
                    name=full_name,
                    element_type='class',
                    line=node.lineno,
                    column=node.col_offset
                )
                classes.add(code_element)
        return classes

    def _collect_function_names(self, tree, file_path: Path) -> Set[CodeElement]:
        functions = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                full_name = self._get_full_name(node)
                code_element = CodeElement(
                    file=file_path,
                    name=full_name,
                    element_type='function',
                    line=node.lineno,
                    column=node.col_offset
                )
                functions.add(code_element)
        return functions

    def _collect_variable_names(self, tree, file_path: Path) -> Set[CodeElement]:
        variables = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        code_element = CodeElement(
                            file=file_path,
                            name=target.id,
                            element_type='variable',
                            line=target.lineno,
                            column=target.col_offset
                        )
                        variables.add(code_element)
        return variables

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))