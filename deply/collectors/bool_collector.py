from typing import Any, Dict, List, Set

from deply.models.code_element import CodeElement
from .base_collector import BaseCollector


class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.config = config
        self.paths = paths
        self.exclude_files = exclude_files

    def collect(self) -> Set[CodeElement]:
        must_elements = self._collect_elements(self.config.get('must', []))
        any_of_elements = self._collect_elements(self.config.get('any_of', []))
        must_not_elements = self._collect_elements(self.config.get('must_not', []))

        if must_elements:
            combined_elements = must_elements
        elif any_of_elements:
            combined_elements = any_of_elements
        else:
            combined_elements = set()

        final_elements = combined_elements - must_not_elements

        return final_elements

    def _collect_elements(self, collector_configs: List[Dict[str, Any]]) -> Set[CodeElement]:
        elements_set = set()
        for collector_config in collector_configs:
            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)
            elements_set.update(collector.collect())
        return elements_set