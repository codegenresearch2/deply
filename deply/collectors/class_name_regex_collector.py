import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import annotate_parent

class ClassNameRegexCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.regex_pattern = config.get('class_name_regex', '')
        self.exclude_files_regex_pattern = config.get('exclude_files_regex', '')
        self.regex = re.compile(self.regex_pattern)
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        all_files = self.get_all_files()

        for file_path in all_files:
            tree = self.parse_file(file_path)
            if tree is None:
                continue
            annotate_parent(tree)
            classes = self.get_matching_classes(tree, file_path)
            collected_elements.update(classes)

        return collected_elements

    def get_all_files(self) -> List[Path]:
        all_files = []

        for base_path in self.paths:
            if not base_path.exists():
                continue

            files = [f for f in base_path.rglob('*.py') if f.is_file()]

            # Apply exclude patterns
            files = [f for f in files if not self.is_excluded(f)]

            all_files.extend(files)

        return all_files

    def is_excluded(self, file_path: Path) -> bool:
        # Apply global exclude patterns
        relative_path = str(file_path.relative_to(self.paths[0]))
        if any(pattern.search(relative_path) for pattern in self.exclude_files):
            return True

        # Apply collector-specific exclude pattern
        if self.exclude_regex and self.exclude_regex.match(relative_path):
            return True

        return False

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def get_matching_classes(self, tree, file_path: Path) -> Set[CodeElement]:
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

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))