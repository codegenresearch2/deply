from typing import Any, Dict, List, Set
from pathlib import Path
import ast

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
        return self._collect_elements()

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        self.initialize_collectors()
        return self._match_in_file(file_ast, file_path)

    def _collect_elements(self) -> Set[CodeElement]:
        must_sets = [collector.collect() for collector in self.must_collectors]
        any_of_sets = [collector.collect() for collector in self.any_of_collectors]
        must_not_elements = set.union(*[collector.collect() for collector in self.must_not_collectors]) if self.must_not_collectors else set()

        must_elements = set.intersection(*must_sets) if must_sets else set()
        any_of_elements = set.union(*any_of_sets) if any_of_sets else set()

        combined_elements = must_elements & any_of_elements if must_elements and any_of_elements else (must_elements or any_of_elements)
        final_elements = combined_elements - must_not_elements

        return final_elements

    def _match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        must_sets = [collector.match_in_file(file_ast, file_path) for collector in self.must_collectors]
        any_of_sets = [collector.match_in_file(file_ast, file_path) for collector in self.any_of_collectors]
        must_not_elements = set.union(*[collector.match_in_file(file_ast, file_path) for collector in self.must_not_collectors]) if self.must_not_collectors else set()

        must_elements = set.intersection(*must_sets) if must_sets else set()
        any_of_elements = set.union(*any_of_sets) if any_of_sets else set()

        combined_elements = must_elements & any_of_elements if must_elements and any_of_elements else (must_elements or any_of_elements)
        final_elements = combined_elements - must_not_elements

        return final_elements