import ast
import re
from pathlib import Path
from typing import List, Set

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement

class DirectoryCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.directories = config.get("directories", [])
        self.recursive = config.get("recursive", True)
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.element_type = config.get("element_type", "")  # 'class', 'function', 'variable'

        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        # Exclude files based on global and collector-specific patterns
        if not self.is_file_included(file_path):
            return set()

        elements = set()

        if not self.element_type or self.element_type == 'class':
            elements.update(self.get_class_names(file_ast, file_path))

        if not self.element_type or self.element_type == 'function':
            elements.update(self.get_function_names(file_ast, file_path))

        if not self.element_type or self.element_type == 'variable':
            elements.update(self.get_variable_names(file_ast, file_path))

        return elements

    def get_class_names(self, tree: ast.AST, file_path: Path) -> Set[CodeElement]:
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

    def get_function_names(self, tree: ast.AST, file_path: Path) -> Set[CodeElement]:
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

    def get_variable_names(self, tree: ast.AST, file_path: Path) -> Set[CodeElement]:
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

    def is_file_included(self, file_path: Path) -> bool:
        # Check against global exclude patterns
        if any(pattern.search(str(file_path)) for pattern in self.exclude_files):
            return False

        # Check against collector-specific exclude pattern
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return False

        # Check if the file is within the specified directories
        if self.directories and not self.is_in_directories(file_path):
            return False

        return True

    def is_in_directories(self, file_path: Path) -> bool:
        # Check if the file is within any of the specified directories
        for base_path in self.paths:
            for directory in self.directories:
                if file_path.is_relative_to(base_path / directory):
                    return True
        return False