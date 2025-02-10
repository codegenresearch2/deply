from typing import Any, Dict, List, Set

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

        elements_set = set()

        # Collect elements based on must_configs
        must_sets = []
        for collector_config in self.must_configs:
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            must_elements = collector.collect()
            if must_elements:
                must_sets.append(must_elements)

        # Collect elements based on any_of_configs
        any_of_sets = []
        for collector_config in self.any_of_configs:
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            any_of_elements = collector.collect()
            if any_of_elements:
                any_of_sets.append(any_of_elements)

        # Collect elements based on must_not_configs
        must_not_elements = set()
        for collector_config in self.must_not_configs:
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            not_elements = collector.collect()
            if not_elements:
                must_not_elements.update(not_elements)

        # Combine must_sets if any
        if must_sets:
            elements_set = set.intersection(*must_sets)

        # Combine any_of_sets if any
        if any_of_sets:
            if elements_set:
                elements_set = elements_set.union(*any_of_sets)
            else:
                elements_set = set.union(*any_of_sets)

        # Subtract must_not_elements
        final_elements = elements_set - must_not_elements if elements_set else set()

        return final_elements