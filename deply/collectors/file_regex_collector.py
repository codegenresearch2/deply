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

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        # Check global exclude patterns
        if any(pattern.search(str(file_path)) for pattern in self.exclude_files):
            return set()

        # Check collector-specific exclude pattern
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return set()

        # Check if file matches the given regex
        # Note: We consider the relative path to each base path and if any matches, we include.
        # If no base path matches, fallback to absolute.
        matched = False
        for base_path in self.paths:
            try:
                relative_path = str(file_path.relative_to(base_path))
                if self.regex.match(relative_path):
                    matched = True
                    break
            except ValueError:
                pass

        if not matched:
            # If no relative matched, check full path as fallback
            if self.regex.match(str(file_path)):
                matched = True

        if not matched:
            return set()

        elements = set()
        if not self.element_type or self.element_type == 'class':
            elements.update(self.get_class_names(file_ast, file_path))
        if not self.element_type or self.element_type == 'function':
            elements.update(self.get_function_names(file_ast, file_path))
        if not self.element_type or self.element_type == 'variable':
            elements.update(self.get_variable_names(file_ast, file_path))

        return elements

    def get_class_names(self, tree, file_path: Path) -> Set[CodeElement]:
        #self.annotate_parent(tree)
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

    def get_function_names(self, tree, file_path: Path) -> Set[CodeElement]:
        #self.annotate_parent(tree)
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

    def get_variable_names(self, tree, file_path: Path) -> Set[CodeElement]:
        # Variables don't need parent annotation for naming
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

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
