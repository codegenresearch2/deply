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
        must_sets = []
        for collector in self.must_collectors:
            elements = collector.collect()
            if elements:
                must_sets.append(elements)

        any_of_sets = []
        for collector in self.any_of_collectors:
            elements = collector.collect()
            if elements:
                any_of_sets.append(elements)

        must_not_elements = set()
        for collector in self.must_not_collectors:
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

        combined_elements = must_elements & any_of_elements
        final_elements = combined_elements - must_not_elements

        return final_elements

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        must_sets = []
        for collector in self.must_collectors:
            elements = collector.match_in_file(file_ast, file_path)
            if elements:
                must_sets.append(elements)

        any_of_sets = []
        for collector in self.any_of_collectors:
            elements = collector.match_in_file(file_ast, file_path)
            if elements:
                any_of_sets.append(elements)

        must_not_elements = set()
        for collector in self.must_not_collectors:
            elements = collector.match_in_file(file_ast, file_path)
            must_not_elements.update(elements)

        if must_sets:
            must_elements = set.intersection(*must_sets)
        else:
            must_elements = set()

        if any_of_sets:
            any_of_elements = set.union(*any_of_sets)
        else:
            any_of_elements = set()

        combined_elements = must_elements & any_of_elements
        final_elements = combined_elements - must_not_elements

        return final_elements