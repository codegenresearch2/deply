from typing import Any, Dict, List, Set\\\nfrom deply.models.code_element import CodeElement\\\\"nfrom .base_collector import BaseCollector\\\\"nfrom pathlib import Path\\\\"nimport ast\\\\"n\\\\"nclass BoolCollector(BaseCollector):\\\\"n    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):\\\\"n        self.config = config\\\\"n        self.paths = paths\\\\"n        self.exclude_files = exclude_files\\\\"n        self.must_collectors = [CollectorFactory.create(cfg, paths, exclude_files) for cfg in config.get('must', [])]\\\\"n        self.any_of_collectors = [CollectorFactory.create(cfg, paths, exclude_files) for cfg in config.get('any_of', [])]\\\\"n        self.must_not_configs = config.get('must_not', [])\\\\"n\\\\"n    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:\\\\"n        must_elements = {element for collector in self.must_collectors for element in collector.match_in_file(file_ast, file_path)}\\\\"n        any_of_elements = {element for collector in self.any_of_collectors for element in collector.match_in_file(file_ast, file_path)}\\\\"n        combined_elements = must_elements & any_of_elements if must_elements and any_of_elements else set()\\\\"n        must_not_elements = {element for cfg in self.must_not_configs for element in CollectorFactory.create(cfg, self.paths, self.exclude_files).match_in_file(file_ast, file_path)}\\\\"n        final_elements = combined_elements - must_not_elements\\\\"n        return final_elements\\\\"n