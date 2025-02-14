import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.collectors.class_name_regex_collector import ClassNameRegexCollector
from deply.collectors.class_inherits_collector import ClassInheritsCollector

class EnhancedFileRegexCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.collectors = self._setup_collectors(config, paths, exclude_files)

    def _setup_collectors(self, config: dict, paths: List[str], exclude_files: List[str]):
        collectors = []
        if config.get("regex"):
            collectors.append(ClassNameRegexCollector(config, paths, exclude_files))
        if config.get("base_class"):
            collectors.append(ClassInheritsCollector(config, paths, exclude_files))
        return collectors

    def collect(self) -> Set[CodeElement]:
        all_files = self.get_all_files()
        collected_elements = set()

        for file_path, base_path in all_files:
            elements = self.get_elements_in_file(file_path)
            collected_elements.update(elements)

        return collected_elements

    def get_all_files(self) -> List[Tuple[Path, Path]]:
        all_files = []
        exclude_regex = self.collectors[0].exclude_regex if self.collectors else None

        for base_path in self.paths:
            if not base_path.exists():
                continue

            files = [f for f in base_path.rglob('*.py') if f.is_file()]

            # Apply collector-specific exclude pattern
            if exclude_regex:
                files = [
                    f for f in files
                    if not exclude_regex.match(str(f.relative_to(base_path)))
                ]

            # Collect files along with their base path
            files_with_base = [(f, base_path) for f in files]
            all_files.extend(files_with_base)

        return all_files

    def get_elements_in_file(self, file_path: Path) -> Set[CodeElement]:
        elements = set()
        tree = self.parse_file(file_path)
        if tree is None:
            return elements

        for collector in self.collectors:
            elements.update(collector.match_in_file(tree, file_path))

        return elements

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None