import ast
import re
from pathlib import Path
from typing import List, Set

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement


class DirectoryCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.directories = config.get('directories', [])
        self.recursive = config.get('recursive', True)
        self.exclude_files_regex_pattern = config.get('exclude_files_regex', '')
        self.element_type = config.get('element_type', '')

        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None
        self.base_paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return set()

        if not self.is_in_directories(file_path):
            return set()

        elements = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.ClassDef) and (not self.element_type or self.element_type == 'class'):
                elements.update(self.get_class_names(node, file_path))
            elif isinstance(node, ast.FunctionDef) and (not self.element_type or self.element_type == 'function'):
                elements.update(self.get_function_names(node, file_path))
            elif isinstance(node, ast.Assign) and (not self.element_type or self.element_type == 'variable'):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        elements.update(self.get_variable_names(target, file_path))
        return elements

    def get_class_names(self, node: ast.ClassDef, file_path: Path) -> Set[CodeElement]:
        classes = set()
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

    def get_function_names(self, node: ast.FunctionDef, file_path: Path) -> Set[CodeElement]:
        functions = set()
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

    def get_variable_names(self, node: ast.Name, file_path: Path) -> Set[CodeElement]:
        variables = set()
        code_element = CodeElement(
            file=file_path,
            name=node.id,
            element_type='variable',
            line=node.lineno,
            column=node.col_offset
        )
        variables.add(code_element)
        return variables

    def is_in_directories(self, file_path: Path) -> bool:
        try:
            relative_path = str(file_path.relative_to(self.base_paths[0]))
            return any(directory in relative_path for directory in self.directories)
        except ValueError:
            return False

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node