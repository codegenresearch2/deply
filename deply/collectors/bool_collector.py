from typing import Any, Dict, List, Set
from deply.models.code_element import CodeElement
from .base_collector import BaseCollector


class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.config = config
        self.paths = paths
        self.exclude_files = exclude_files

    def collect(self) -> Set[CodeElement]:
        from .collector_factory import CollectorFactory

        must_sets = self._collect_elements(self.config.get('must', []))
        any_of_sets = self._collect_elements(self.config.get('any_of', []))
        must_not_elements = self._collect_elements(self.config.get('must_not', []))

        combined_elements = self._combine_elements(must_sets, any_of_sets)
        final_elements = combined_elements - must_not_elements

        return final_elements

    def _collect_elements(self, collector_configs: List[Dict[str, Any]]) -> List[Set[CodeElement]]:
        elements_sets = []
        for collector_config in collector_configs:
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            elements_sets.append(collector.collect())
        return elements_sets

    def _combine_elements(self, must_sets: List[Set[CodeElement]], any_of_sets: List[Set[CodeElement]]) -> Set[CodeElement]:
        if must_sets:
            must_elements = set.intersection(*must_sets)
        else:
            must_elements = None

        if any_of_sets:
            any_of_elements = set.union(*any_of_sets)
        else:
            any_of_elements = None

        if must_elements is not None and any_of_elements is not None:
            return must_elements & any_of_elements
        elif must_elements is not None:
            return must_elements
        elif any_of_elements is not None:
            return any_of_elements
        else:
            return set()