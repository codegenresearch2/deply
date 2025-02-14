from typing import Any, Dict, List, Set
import ast
from pathlib import Path

from deply.models.code_element import CodeElement
from .base_collector import BaseCollector
from .collector_factory import CollectorFactory

class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.paths = paths
        self.exclude_files = exclude_files
        self.config = config

    def collect(self) -> Set[CodeElement]:
        # Consolidate collector execution into a single method
        def collect_elements(config_key: str) -> Set[CodeElement]:
            elements_set = []
            for collector_config in self.config.get(config_key, []):
                collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
                elements = collector.collect()
                elements_set.append(elements)
            return elements_set

        # Collect elements for each configuration
        must_sets = collect_elements('must')
        any_of_sets = collect_elements('any_of')
        must_not_sets = collect_elements('must_not')

        # Calculate final elements
        must_elements = set.intersection(*must_sets) if must_sets else set()
        any_of_elements = set.union(*any_of_sets) if any_of_sets else set()
        must_not_elements = set.union(*must_not_sets) if must_not_sets else set()

        combined_elements = must_elements & any_of_elements
        final_elements = combined_elements - must_not_elements

        return final_elements

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> set[CodeElement]:
        # Include file AST processing and abstract collection logic into a method
        # This method is required by the abstract base class but not used in this collector
        return set()