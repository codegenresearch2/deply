from typing import Any, Dict, List, Set
import ast
from pathlib import Path

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
        must_sets = [collector.collect() for collector in self.must_collectors]
        any_of_sets = [collector.collect() for collector in self.any_of_collectors]
        must_not_elements = set.union(*[collector.collect() for collector in self.must_not_collectors])

        if must_sets:
            must_elements = set.intersection(*must_sets)
        else:
            must_elements = set()

        if any_of_sets:
            any_of_elements = set.union(*any_of_sets)
        else:
            any_of_elements = set()

        if must_elements and any_of_elements:
            combined_elements = must_elements & any_of_elements
        elif must_elements:
            combined_elements = must_elements
        elif any_of_elements:
            combined_elements = any_of_elements
        else:
            combined_elements = set()

        final_elements = combined_elements - must_not_elements

        return final_elements

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.BoolOp):
                elements.add(CodeElement(file_path, node.lineno, node.col_offset, 'bool_expression'))
        return elements