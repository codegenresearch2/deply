from typing import Any, Dict, List, Set\nfrom deply.models.code_element import CodeElement\nfrom .base_collector import BaseCollector\nfrom pathlib import Path\nimport ast\n\nclass BoolCollector(BaseCollector):\n    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):\n        self.config = config\n        self.paths = paths\n        self.exclude_files = exclude_files\n        self.must_configs = config.get('must', [])\n        self.any_of_configs = config.get('any_of', [])\n        self.must_not_configs = config.get('must_not', [])\n        self.must_elements = None\n        self.any_of_elements = None\n\n    def collect(self) -> Set[CodeElement]:\n        from .collector_factory import CollectorFactory\n\n        def collect_elements(configs: List[Dict[str, Any]]) -> Set[CodeElement]:\n            elements_sets = []\n            for collector_config in configs:\n                collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)\n                elements_sets.append(collector.collect())\n            return set.intersection(*elements_sets) if elements_sets else set()\n\n        self.must_elements = collect_elements(self.must_configs)\n        self.any_of_elements = collect_elements(self.any_of_configs)\n\n        combined_elements = (self.must_elements & self.any_of_elements) if self.must_elements is not None and self.any_of_elements is not None else self.must_elements or self.any_of_elements or set()\n\n        must_not_elements = set()\n        for collector_config in self.must_not_configs:\n            collector = CollectorFactory.create(collector_config, self.paths, self.exclude_files)\n            must_not_elements.update(collector.collect())\n\n        final_elements = combined_elements - must_not_elements\n\n        return final_elements