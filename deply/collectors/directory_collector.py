import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.collectors.class_name_regex_collector import ClassNameRegexCollector
from deply.collectors.class_inherits_collector import ClassInheritsCollector

class DirectoryCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.directories = config.get("directories", [])
        self.recursive = config.get("recursive", True)
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.element_type = config.get("element_type", "")  # 'class', 'function', 'variable'
        self.class_name_regex_pattern = config.get("class_name_regex", "")
        self.base_class = config.get("base_class", "")

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

            for directory in self.directories:
                dir_path = base_path / directory
                if dir_path.exists() and dir_path.is_dir():
                    files = self.get_files_in_directory(dir_path)
                    all_files.extend([(f, base_path) for f in files])

        return all_files

    def get_files_in_directory(self, dir_path: Path) -> List[Path]:
        if self.recursive:
            files = [f for f in dir_path.rglob('*.py') if f.is_file()]
        else:
            files = [f for f in dir_path.glob('*.py') if f.is_file()]

        files = [f for f in files if not self.is_excluded(f, dir_path)]

        return files

    def is_excluded(self, file_path: Path, base_path: Path) -> bool:
        relative_path = str(file_path.relative_to(base_path))
        return any(pattern.search(relative_path) for pattern in self.exclude_files) or (self.exclude_regex and self.exclude_regex.match(relative_path))

    def get_elements_in_file(self, file_path: Path) -> Set[CodeElement]:
        elements = set()
        tree = self.parse_file(file_path)
        if tree is None:
            return elements

        if self.element_type == 'class':
            if self.class_name_regex_pattern:
                elements.update(self.get_matching_class_names(tree, file_path))
            elif self.base_class:
                elements.update(self.get_inheriting_class_names(tree, file_path))
            else:
                elements.update(self.get_class_names(tree, file_path))
        elif self.element_type == 'function':
            elements.update(self.get_function_names(tree, file_path))
        elif self.element_type == 'variable':
            elements.update(self.get_variable_names(tree, file_path))

        return elements

    def get_matching_class_names(self, tree, file_path: Path) -> Set[CodeElement]:
        collector = ClassNameRegexCollector(config={'class_name_regex': self.class_name_regex_pattern, 'exclude_files_regex': self.exclude_files_regex_pattern}, paths=[], exclude_files=[])
        return collector.match_in_file(tree, file_path)

    def get_inheriting_class_names(self, tree, file_path: Path) -> Set[CodeElement]:
        collector = ClassInheritsCollector(config={'base_class': self.base_class, 'exclude_files_regex': self.exclude_files_regex_pattern}, paths=[], exclude_files=[])
        return collector.match_in_file(tree, file_path)

    # Remaining methods remain the same