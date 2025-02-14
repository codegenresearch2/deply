from typing import Any, Dict, List, Set

from deply.collectors.base_collector import BaseCollector
from deply.collectors.collector_factory import CollectorFactory
from deply.models.code_element import CodeElement

class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.config = config
        self.paths = paths
        self.exclude_files = exclude_files

    def collect_elements(self, configs: List[Dict[str, Any]]) -> Set[CodeElement]:
        elements_sets = []
        for collector_config in configs:
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            elements = collector.collect()
            elements_sets.append(elements)
        return elements_sets

    def process_elements(self, elements_sets: List[Set[CodeElement]], operation: str) -> Set[CodeElement]:
        if not elements_sets:
            return set()
        if operation == 'intersection':
            return set.intersection(*elements_sets)
        elif operation == 'union':
            return set.union(*elements_sets)

    def collect(self) -> Set[CodeElement]:
        must_elements = self.process_elements(self.collect_elements(self.config.get('must', [])), 'intersection')
        any_of_elements = self.process_elements(self.collect_elements(self.config.get('any_of', [])), 'union')
        must_not_elements = set.union(*self.collect_elements(self.config.get('must_not', [])))

        combined_elements = must_elements & any_of_elements
        final_elements = combined_elements - must_not_elements

        return final_elements

In the rewritten code, I have separated the collection and processing of elements into two methods. This improves code organization and readability. The `collect_elements` method is responsible for creating collectors based on the given configurations and collecting elements. The `process_elements` method performs set operations based on the operation type ('intersection' or 'union'). The `collect` method uses these helper methods to gather elements according to the boolean logic specified in the config. This makes the collector more flexible and customizable.