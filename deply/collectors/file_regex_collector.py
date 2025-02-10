import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name

class FileRegexCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.regex_pattern = config.get("regex", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.element_type = config.get("element_type", "")  # 'class', 'function', 'variable'
        self.base_class = config.get("base_class", "")

        self.regex = re.compile(self.regex_pattern)
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def collect(self) -> Set[CodeElement]:
        all_files = self.get_all_files()
        collected_elements = set()

        for file_path in all_files:
            elements = self.get_elements_in_file(file_path)
            collected_elements.update(elements)

        return collected_elements

    def get_all_files(self) -> List[Path]:
        all_files = []

        for base_path in self.paths:
            if not base_path.exists():
                continue

            files = [f for f in base_path.rglob('*.py') if f.is_file()]

            # Apply global exclude patterns
            files = [f for f in files if not any(pattern.search(str(f)) for pattern in self.exclude_files)]

            # Apply collector-specific exclude pattern
            if self.exclude_regex:
                files = [f for f in files if not self.exclude_regex.match(str(f))]

            all_files.extend(files)

        return all_files

    def get_elements_in_file(self, file_path: Path) -> Set[CodeElement]:
        elements = set()
        tree = self.parse_file(file_path)
        if tree is None:
            return elements

        import_aliases = get_import_aliases(tree)

        if not self.element_type or self.element_type == 'class':
            elements.update(self.get_class_names(tree, file_path, import_aliases))

        if not self.element_type or self.element_type == 'function':
            elements.update(self.get_function_names(tree, file_path))

        if not self.element_type or self.element_type == 'variable':
            elements.update(self.get_variable_names(tree, file_path))

        return elements

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def get_class_names(self, tree, file_path: Path, import_aliases: dict) -> Set[CodeElement]:
        classes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self.base_class:
                    for base in node.bases:
                        base_name = get_base_name(base, import_aliases)
                        if base_name == self.base_class or base_name.endswith(f".{self.base_class}"):
                            full_name = self._get_full_name(node)
                            code_element = CodeElement(file=file_path, name=full_name, element_type="class", line=node.lineno, column=node.col_offset)
                            classes.add(code_element)
                else:
                    full_name = self._get_full_name(node)
                    code_element = CodeElement(file=file_path, name=full_name, element_type="class", line=node.lineno, column=node.col_offset)
                    classes.add(code_element)
        return classes

    def get_function_names(self, tree, file_path: Path) -> Set[CodeElement]:
        return self._get_elements_by_type(tree, file_path, ast.FunctionDef, "function")

    def get_variable_names(self, tree, file_path: Path) -> Set[CodeElement]:
        variables = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        code_element = CodeElement(file=file_path, name=target.id, element_type="variable", line=target.lineno, column=target.col_offset)
                        variables.add(code_element)
        return variables

    def _get_elements_by_type(self, tree, file_path: Path, node_type, element_type: str) -> Set[CodeElement]:
        elements = set()
        for node in ast.walk(tree):
            if isinstance(node, node_type):
                full_name = self._get_full_name(node)
                code_element = CodeElement(file=file_path, name=full_name, element_type=element_type, line=node.lineno, column=node.col_offset)
                elements.add(code_element)
        return elements

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, "parent", None)
        return ".".join(reversed(names))