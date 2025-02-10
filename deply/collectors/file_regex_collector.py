import ast
import re
from pathlib import Path
from typing import List, Set

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

        # Initialize base_path attribute
        self.base_path = Path(paths[0]) if paths else Path.cwd()

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        # Apply exclude patterns
        if self.is_excluded(file_path):
            return set()

        elements = set()

        if self.element_type in ['class', '']:
            elements.update(self.get_class_names(file_ast, file_path))

        if self.element_type in ['function', '']:
            elements.update(self.get_function_names(file_ast, file_path))

        if self.element_type in ['variable', '']:
            elements.update(self.get_variable_names(file_ast, file_path))

        return elements

    def is_excluded(self, file_path: Path) -> bool:
        relative_path = str(file_path.relative_to(self.base_path))
        absolute_path = str(file_path.absolute())

        # Check global exclude patterns
        if any(pattern.search(relative_path) or pattern.search(absolute_path) for pattern in self.exclude_files):
            return True

        # Check collector-specific exclude pattern
        if self.exclude_regex and (self.exclude_regex.match(relative_path) or self.exclude_regex.match(absolute_path)):
            return True

        return False

    def get_class_names(self, tree, file_path: Path) -> Set[CodeElement]:
        classes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and self.regex.match(node.name):
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

    def get_function_names(self, tree, file_path: Path) -> Set[CodeElement]:
        functions = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and self.regex.match(node.name):
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

    def get_variable_names(self, tree, file_path: Path) -> Set[CodeElement]:
        variables = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and self.regex.match(target.id):
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