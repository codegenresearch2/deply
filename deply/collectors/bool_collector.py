from typing import Any, Dict, List, Set
from pathlib import Path
import ast

from deply.models.code_element import CodeElement
from .base_collector import BaseCollector

class FlexibleBoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.paths = paths
        self.exclude_files = exclude_files
        self.must_configs = config.get('must', [])
        self.any_of_configs = config.get('any_of', [])
        self.must_not_configs = config.get('must_not', [])

    def collect(self) -> Set[CodeElement]:
        from .collector_factory import CollectorFactory

        must_sets = []
        for collector_config in self.must_configs:
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            elements = collector.collect()
            must_sets.append(elements)

        any_of_sets = []
        for collector_config in self.any_of_configs:
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            elements = collector.collect()
            any_of_sets.append(elements)

        must_not_elements = set()
        for collector_config in self.must_not_configs:
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            elements = collector.collect()
            must_not_elements.update(elements)

        if must_sets:
            must_elements = set.intersection(*must_sets)
        else:
            must_elements = set()

        if any_of_sets:
            any_of_elements = set.union(*any_of_sets)
        else:
            any_of_elements = set()

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
        from .collector_factory import CollectorFactory

        elements = set()
        for collector_config in self.must_configs + self.any_of_configs + self.must_not_configs:
            collector = CollectorFactory.create(collector_config, [str(file_path)], self.exclude_files)
            elements.update(collector.match_in_file(file_ast, file_path))

        return elements