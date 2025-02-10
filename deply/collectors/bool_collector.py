from typing import Any, Dict, List, Set
from pathlib import Path
import ast

from deply.models.code_element import CodeElement
from .base_collector import BaseCollector
from .collector_factory import CollectorFactory

class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.paths = paths
        self.exclude_files = exclude_files
        self.must_collectors = [CollectorFactory.create(collector_config, paths, exclude_files) for collector_config in config.get('must', [])]
        self.any_of_collectors = [CollectorFactory.create(collector_config, paths, exclude_files) for collector_config in config.get('any_of', [])]
        self.must_not_collectors = [CollectorFactory.create(collector_config, paths, exclude_files) for collector_config in config.get('must_not', [])]

    def collect(self) -> Set[CodeElement]:
        must_elements = set.intersection(*[collector.collect() for collector in self.must_collectors]) if self.must_collectors else set()
        any_of_elements = set.union(*[collector.collect() for collector in self.any_of_collectors]) if self.any_of_collectors else set()
        must_not_elements = set.union(*[collector.collect() for collector in self.must_not_collectors]) if self.must_not_collectors else set()

        if must_elements and any_of_elements:
            combined_elements = must_elements & any_of_elements
        elif must_elements:
            combined_elements = must_elements
        elif any_of_elements:
            combined_elements = any_of_elements
        else:
            combined_elements = set()

        final_elements = combined_elements - must_not_elements

        return final_elements

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for collector in self.must_collectors + self.any_of_collectors + self.must_not_collectors:
            elements.update(collector.match_in_file(file_ast, file_path))

        return elements