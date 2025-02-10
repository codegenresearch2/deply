import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name

class DirectoryCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.directories = config.get("directories", [])
        self.recursive = config.get("recursive", True)
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.element_type = config.get("element_type", "")  # 'class', 'function', 'variable'

        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        all_files = self.get_all_files()

        for file_path, base_path in all_files:
            elements = self.get_elements_in_file(file_path)
            collected_elements.update(elements)

        return collected_elements

    def get_all_files(self) -> List[Tuple[Path, Path]]:
        all_files = []

        for base_path in self.paths:
            if not base_path.exists():
                continue

            files = self.get_files_in_directory(base_path)
            files_with_base = [(f, base_path) for f in files]
            all_files.extend(files_with_base)

        return all_files

    def get_files_in_directory(self, base_path: Path) -> List[Path]:
        if self.recursive:
            files = [f for f in base_path.rglob('*.py') if f.is_file()]
        else:
            files = [f for f in base_path.glob('*.py') if f.is_file()]

        files = [f for f in files if self.is_file_included(f, base_path)]
        return files

    def is_file_included(self, file_path: Path, base_path: Path) -> bool:
        relative_path = str(file_path.relative_to(base_path))
        if any(pattern.search(relative_path) for pattern in self.exclude_files):
            return False
        if self.exclude_regex and self.exclude_regex.match(relative_path):
            return False
        if self.directories and not any(file_path.is_relative_to(base_path / directory) for directory in self.directories):
            return False
        return True

    def get_elements_in_file(self, file_path: Path) -> Set[CodeElement]:
        elements = set()
        tree = self.parse_file(file_path)
        if tree is None:
            return elements

        if not self.element_type or self.element_type == 'class':
            elements.update(self.get_elements(tree, file_path, ast.ClassDef, 'class'))

        if not self.element_type or self.element_type == 'function':
            elements.update(self.get_elements(tree, file_path, ast.FunctionDef, 'function'))

        if not self.element_type or self.element_type == 'variable':
            elements.update(self.get_elements(tree, file_path, ast.Assign, 'variable', self.get_variable_names))

        return elements

    def get_elements(self, tree, file_path: Path, node_type, element_type: str, extract_func=None) -> Set[CodeElement]:
        elements = set()
        for node in ast.walk(tree):
            if isinstance(node, node_type):
                if extract_func:
                    names = extract_func(node)
                else:
                    names = [self._get_full_name(node)]
                for name in names:
                    code_element = CodeElement(
                        file=file_path,
                        name=name,
                        element_type=element_type,
                        line=node.lineno,
                        column=node.col_offset
                    )
                    elements.add(code_element)
        return elements

    def get_variable_names(self, node) -> List[str]:
        names = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
        return names

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))