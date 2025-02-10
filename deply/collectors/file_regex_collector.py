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

        if not self.element_type or self.element_type == 'class':
            elements.update(self.get_class_names(file_ast, file_path))

        if not self.element_type or self.element_type == 'function':
            elements.update(self.get_function_names(file_ast, file_path))

        if not self.element_type or self.element_type == 'variable':
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

    # Rest of the code remains the same