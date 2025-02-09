import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement


class FileRegexCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.regex_pattern = config.get('regex', '')
        self.exclude_files_regex_pattern = config.get('exclude_files_regex', '')
        self.element_type = config.get('element_type', '')
        self.regex = re.compile(self.regex_pattern)
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None
        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def collect(self) -> Set[CodeElement]:
        all_files = self.get_all_files()
        collected_elements = set()
        for file_path, base_path in all_files:
            relative_path = str(file_path.relative_to(base_path))
            if self.regex.match(relative_path):
                elements = self.get_elements_in_file(file_path)
                collected_elements.update(elements)
        return collected_elements

    def get_all_files(self) -> List[Tuple[Path, Path]]:
        all_files = []
        for base_path in self.paths:
            if not base_path.exists():
                continue
            files = [f for f in base_path.rglob('*.py') if f.is_file()]
            files = [f for f in files if not any(pattern.search(str(f.relative_to(base_path))) for pattern in self.exclude_files)]
            if self.exclude_regex:
                files = [f for f in files if not self.exclude_regex.match(str(f.relative_to(base_path)))]
            all_files.extend([(f, base_path) for f in files])
        return all_files

    def get_elements_in_file(self, file_path: Path) -> Set[CodeElement]:
        elements = set()
        tree = self.parse_file(file_path)
        if tree is None:
            return elements
        if not self.element_type or self.element_type == 'class':
            elements.update(self._collect_elements(tree, file_path, ast.ClassDef))
        if not self.element_type or self.element_type == 'function':
            elements.update(self._collect_elements(tree, file_path, ast.FunctionDef))
        if not self.element_type or self.element_type == 'variable':
            elements.update(self._collect_elements(tree, file_path, ast.Assign))
        return elements

    def _collect_elements(self, tree, file_path: Path, element_type):
        elements = set()
        for node in ast.walk(tree):
            if isinstance(node, element_type):
                if self.regex.match(node.name):
                    full_name = self._get_full_name(node)
                    code_element = CodeElement(
                        file=file_path,
                        name=full_name,
                        element_type=element_type.__name__.lower(),
                        line=node.lineno,
                        column=node.col_offset
                    )
                    elements.add(code_element)
        return elements

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
