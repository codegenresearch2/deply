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

    def collect(self) -> Set[CodeElement]:
        from .collector_factory import CollectorFactory

        must_elements = self.collect_elements(self.must_configs)
        any_of_elements = self.collect_elements(self.any_of_configs)
        must_not_elements = self.collect_elements(self.must_not_configs)

        if must_elements and any_of_elements:
            combined_elements = must_elements & any_of_elements
        else:
            combined_elements = must_elements or any_of_elements

        final_elements = combined_elements - must_not_elements if combined_elements else set()

        return final_elements

    def collect_elements(self, configs: List[Dict[str, Any]]) -> Set[CodeElement]:
        from .collector_factory import CollectorFactory

        elements = set()
        for collector_config in configs:
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            elements.update(collector.collect())

        return elements

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        from .collector_factory import CollectorFactory

        elements = set()

        for collector_config in self.must_configs:
            collector = CollectorFactory.create(collector_config, [str(file_path)], self.exclude_files)
            elements.update(collector.match_in_file(file_ast, file_path))

        for collector_config in self.any_of_configs:
            collector = CollectorFactory.create(collector_config, [str(file_path)], self.exclude_files)
            elements.update(collector.match_in_file(file_ast, file_path))

        for collector_config in self.must_not_configs:
            collector = CollectorFactory.create(collector_config, [str(file_path)], self.exclude_files)
            elements -= collector.match_in_file(file_ast, file_path)

        return elements