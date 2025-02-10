import ast
import re
from pathlib import Path
from typing import List, Set

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement

class ClassNameRegexCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.regex_pattern = config.get("class_name_regex", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.regex = re.compile(self.regex_pattern)
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None
        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        for base_path in self.paths:
            if base_path.exists():
                files = [f for f in base_path.rglob("*.py") if f.is_file() and not self.is_excluded(f, base_path)]
                for file_path in files:
                    tree = self.parse_file(file_path)
                    if tree is None:
                        continue
                    collected_elements.update(self.match_in_file(tree, file_path))
        return collected_elements

    def is_excluded(self, file_path: Path, base_path: Path) -> bool:
        relative_path = str(file_path.relative_to(base_path))
        return any(pattern.search(relative_path) for pattern in self.exclude_files) or \
               (self.exclude_regex and self.exclude_regex.match(relative_path))

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def match_in_file(self, tree: ast.AST, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and self.regex.match(node.name):
                elements.add(CodeElement(file=file_path, name=self._get_full_name(node), element_type='class', line=node.lineno, column=node.col_offset))
        return elements

    def _get_full_name(self, node):
        names = []
        while isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.append(node.name)
            node = getattr(node, 'parent', None)
        return '.'.join(reversed(names))