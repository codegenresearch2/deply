import ast
from typing import Any, Dict, List, Set
from pathlib import Path
from deply.models.code_element import CodeElement
from .base_collector import BaseCollector

class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.paths = paths
        self.exclude_files = exclude_files
        self.must_configs = config.get('must', [])
        self.any_of_configs = config.get('any_of', [])
        self.must_not_configs = config.get('must_not', [])
        self.must_collectors = [CollectorFactory.create(cfg, paths, exclude_files) for cfg in self.must_configs]
        self.any_of_collectors = [CollectorFactory.create(cfg, paths, exclude_files) for cfg in self.any_of_configs]
        self.must_not_collectors = [CollectorFactory.create(cfg, paths, exclude_files) for cfg in self.must_not_configs]

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for collector in self.must_collectors:
            elements.update(collector.match_in_file(file_ast, file_path))
        return elements

    def collect(self) -> Set[CodeElement]:
        must_elements = set.intersection(*[collector.collect() for collector in self.must_collectors]) if self.must_collectors else set()
        any_of_elements = set.union(*[collector.collect() for collector in self.any_of_collectors]) if self.any_of_collectors else set()
        must_not_elements = set.union(*[collector.collect() for collector in self.must_not_collectors]) if self.must_not_collectors else set()

        final_elements = must_elements & any_of_elements - must_not_elements
        return final_elements