import ast\nfrom abc import ABC, abstractmethod\nfrom pathlib import Path\nfrom typing import Any, Dict, List, Set\n\nfrom deply.models.code_element import CodeElement\nfrom .base_collector import BaseCollector\n\nclass BoolCollector(BaseCollector):\n    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):\n        self.paths = paths\n        self.exclude_files = exclude_files\n        self.must_configs = config.get('must', [])\n        self.any_of_configs = config.get('any_of', [])\n        self.must_not_configs = config.get('must_not', [])\n        self.must_collectors = [CollectorFactory.create(config, self.paths, self.exclude_files) for config in self.must_configs]\n        self.any_of_collectors = [CollectorFactory.create(config, self.paths, self.exclude_files) for config in self.any_of_configs]\n        self.must_not_collector = CollectorFactory.create(self.must_not_configs[0], self.paths, self.exclude_files) if self.must_not_configs else None\n\n    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:\n        must_elements = set()\n        any_of_elements = set()\n\n        for collector in self.must_collectors:\n            must_elements.update(collector.match_in_file(file_ast, file_path))\n\n        for collector in self.any_of_collectors:\n            any_of_elements.update(collector.match_in_file(file_ast, file_path))\n\n        if self.must_not_collector:\n            must_not_elements = set(any_of_elements).intersection(self.must_not_collector.match_in_file(file_ast, file_path))\n        else:\n            must_not_elements = set()\n\n        combined_elements = must_elements.intersection(any_of_elements)\n        final_elements = combined_elements - set(must_not_elements)\n\n        return final_elements\n