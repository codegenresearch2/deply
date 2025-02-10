from typing import Any, Dict, List, Set
from pathlib import Path
import ast

from deply.models.code_element import CodeElement
from .base_collector import BaseCollector
from .collector_factory import CollectorFactory

class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.paths = paths
        self.exclude_files = exclude_files
        self.must_collectors = [CollectorFactory.create(c, paths, exclude_files) for c in config.get('must', [])]
        self.any_of_collectors = [CollectorFactory.create(c, paths, exclude_files) for c in config.get('any_of', [])]
        self.must_not_collectors = [CollectorFactory.create(c, paths, exclude_files) for c in config.get('must_not', [])]

    def collect(self) -> Set[CodeElement]:
        return self._collect_elements()

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        return self._match_in_file(file_ast, file_path)

    def _collect_elements(self) -> Set[CodeElement]:
        must_elements = self._get_elements(self.must_collectors)
        any_of_elements = self._get_elements(self.any_of_collectors)
        must_not_elements = self._get_elements(self.must_not_collectors)

        if must_elements and any_of_elements:
            combined_elements = must_elements & any_of_elements
        else:
            combined_elements = must_elements or any_of_elements

        final_elements = combined_elements - must_not_elements

        return final_elements

    def _match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        must_elements = self._get_elements_in_file(self.must_collectors, file_ast, file_path)
        any_of_elements = self._get_elements_in_file(self.any_of_collectors, file_ast, file_path)
        must_not_elements = self._get_elements_in_file(self.must_not_collectors, file_ast, file_path)

        if must_elements and any_of_elements:
            combined_elements = must_elements & any_of_elements
        else:
            combined_elements = must_elements or any_of_elements

        final_elements = combined_elements - must_not_elements

        return final_elements

    def _get_elements(self, collectors: List[BaseCollector]) -> Set[CodeElement]:
        elements = set()
        for collector in collectors:
            elements.update(collector.collect())
        return elements

    def _get_elements_in_file(self, collectors: List[BaseCollector], file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for collector in collectors:
            elements.update(collector.match_in_file(file_ast, file_path))
        return elements