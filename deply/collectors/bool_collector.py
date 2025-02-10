from typing import Any, Dict, List, Set
from pathlib import Path
import ast

from deply.models.code_element import CodeElement
from .base_collector import BaseCollector
from .collector_factory import CollectorFactory

class FlexibleBoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.paths = paths
        self.exclude_files = exclude_files
        self.must_collectors = [CollectorFactory.create(collector_config, paths, exclude_files) for collector_config in config.get('must', [])]
        self.any_of_collectors = [CollectorFactory.create(collector_config, paths, exclude_files) for collector_config in config.get('any_of', [])]
        self.must_not_collectors = [CollectorFactory.create(collector_config, paths, exclude_files) for collector_config in config.get('must_not', [])]

    def collect(self) -> Set[CodeElement]:
        def collect_elements(collectors: List[BaseCollector]) -> Set[CodeElement]:
            return set.union(*[collector.collect() for collector in collectors]) if collectors else set()

        must_elements = collect_elements(self.must_collectors)
        any_of_elements = collect_elements(self.any_of_collectors)
        must_not_elements = collect_elements(self.must_not_collectors)

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
        elements = [collector.match_in_file(file_ast, file_path) for collectors in [self.must_collectors, self.any_of_collectors, self.must_not_collectors] for collector in collectors]
        return set.union(*elements) if elements else set()