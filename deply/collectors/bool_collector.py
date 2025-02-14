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

        must_sets = self._collect_elements('must')
        any_of_sets = self._collect_elements('any_of')
        must_not_elements = self._collect_elements('must_not')

        must_elements = self._combine_elements(must_sets, operator='intersection')
        any_of_elements = self._combine_elements(any_of_sets, operator='union')

        combined_elements = self._combine_elements_with_or([must_elements, any_of_elements], operator='intersection')

        final_elements = combined_elements - must_not_elements

        return final_elements

    def _collect_elements(self, key: str) -> List[Set[CodeElement]]:
        elements_sets = []
        for collector_config in self.config.get(key, []):
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            elements_sets.append(set(collector.collect()))
        return elements_sets

    def _combine_elements(self, elements_sets: List[Set[CodeElement]], operator: str) -> Set[CodeElement]:
        if not elements_sets:
            return set()
        combined_elements = elements_sets[0]
        for elements in elements_sets[1:]:
            if operator == 'intersection':
                combined_elements &= elements
            elif operator == 'union':
                combined_elements |= elements
        return combined_elements

    def _combine_elements_with_or(self, elements_lists: List[List[Set[CodeElement]]], operator: str) -> Set[CodeElement]:
        combined_elements = set()
        for elements_list in elements_lists:
            combined_elements |= self._combine_elements(elements_list, operator)
        return combined_elements