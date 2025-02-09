import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

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
        if self.is_excluded(file_path):
            return set()

        if not self.is_in_directories(file_path):
            return set()

        elements = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.ClassDef):
                full_name = self._get_full_name(node)
                code_element = CodeElement(
                    file=file_path,
                    name=full_name,
                    element_type='class',
                    line=node.lineno,
                    column=node.col_offset
                )
                elements.add(code_element)
            elif isinstance(node, ast.FunctionDef):
                full_name = self._get_full_name(node)
                code_element = CodeElement(
                    file=file_path,
                    name=full_name,
                    element_type='function',
                    line=node.lineno,
                    column=node.col_offset
                )
                elements.add(code_element)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        code_element = CodeElement(
                            file=file_path,
                            name=target.id,
                            element_type='variable',
                            line=target.lineno,
                            column=target.col_offset
                        )
                        elements.add(code_element)
        return elements

    def is_excluded(self, file_path: Path) -> bool:
        relative_path = str(file_path.relative_to(self.base_paths[0]))
        return any(pattern.search(relative_path) for pattern in self.exclude_files)

    def is_in_directories(self, file_path: Path) -> bool:
        for directory in self.directories:
            if file_path.is_relative_to(directory):
                return True
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