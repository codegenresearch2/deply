from typing import Any, Dict, List, Set
import ast
from pathlib import Path

from deply.models.code_element import CodeElement
from .base_collector import BaseCollector

class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.paths = paths
        self.exclude_files = exclude_files
        self.must_configs = config.get('must', [])
        self.any_of_configs = config.get('any_of', [])
        self.must_not_configs = config.get('must_not', [])
        self.must_collectors = []
        self.any_of_collectors = []
        self.must_not_collectors = []

    def initialize_collectors(self):
        from .collector_factory import CollectorFactory
        self.must_collectors = [CollectorFactory.create(c, self.paths, self.exclude_files) for c in self.must_configs]
        self.any_of_collectors = [CollectorFactory.create(c, self.paths, self.exclude_files) for c in self.any_of_configs]
        self.must_not_collectors = [CollectorFactory.create(c, self.paths, self.exclude_files) for c in self.must_not_configs]

    def collect(self) -> Set[CodeElement]:
        self.initialize_collectors()
        must_elements = self.collect_elements(self.must_collectors)
        any_of_elements = self.collect_elements(self.any_of_collectors)
        must_not_elements = self.collect_elements(self.must_not_collectors)

        if must_elements is not None and any_of_elements is not None:
            combined_elements = must_elements & any_of_elements
        elif must_elements is not None:
            combined_elements = must_elements
        elif any_of_elements is not None:
            combined_elements = any_of_elements
        else:
            combined_elements = set()

        final_elements = combined_elements - must_not_elements

        return final_elements

    def collect_elements(self, collectors: List[BaseCollector]) -> Set[CodeElement]:
        elements = [collector.collect() for collector in collectors]
        return set.union(*elements) if elements else None

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for collector in self.must_collectors + self.any_of_collectors + self.must_not_collectors:
            elements.update(collector.match_in_file(file_ast, file_path))
        return elements