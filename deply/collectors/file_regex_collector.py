import ast
import re
from pathlib import Path

from .base_collector import BaseCollector
from ..models.code_element import CodeElement


class FileRegexCollector(BaseCollector):
    def __init__(self, config: dict, project_root: Path):
        self.regex_pattern = config.get("regex", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.element_type = config.get("element_type", "")  # 'class', 'function', 'variable'
        self.regex = re.compile(self.regex_pattern)
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None
        self.project_root = project_root

    def collect(self) -> set[CodeElement]:
        all_files = self.get_all_files()
        collected_elements = set()
        for file_path in all_files:
            relative_path = str(file_path.relative_to(self.project_root))
            if self.regex.match(relative_path):
                elements = self.get_elements_in_file(file_path)
                collected_elements.update(elements)

        return collected_elements

    def get_all_files(self):
        all_files = [f for f in self.project_root.rglob('*.py') if f.is_file()]
        if self.exclude_regex:
            all_files = [f for f in all_files if not self.exclude_regex.match(str(f.relative_to(self.project_root)))]
        return all_files

    def get_elements_in_file(self, file_path: Path) -> set[CodeElement]:
        elements = set()
        tree = self.parse_file(file_path)
        if tree is None:
            return elements

        if not self.element_type or self.element_type == 'class':
            elements.update(self.get_class_names(tree, file_path))

        if not self.element_type or self.element_type == 'function':
            elements.update(self.get_function_names(tree, file_path))

        if not self.element_type or self.element_type == 'variable':
            elements.update(self.get_variable_names(tree, file_path))

        return elements

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except SyntaxError:
            return None

    def get_class_names(self, tree, file_path: Path) -> set[CodeElement]:
        classes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                code_element = CodeElement(
                    file=file_path,
                    name=node.name,
                    element_type='class',
                    line=node.lineno,
                    column=node.col_offset
                )
                classes.add(code_element)
        return classes

    def get_function_names(self, tree, file_path: Path) -> set[CodeElement]:
        functions = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                code_element = CodeElement(
                    file=file_path,
                    name=node.name,
                    element_type='function',
                    line=node.lineno,
                    column=node.col_offset
                )
                functions.add(code_element)
        return functions

    def get_variable_names(self, tree, file_path: Path) -> set[CodeElement]:
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
