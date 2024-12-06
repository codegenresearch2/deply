import ast
from pathlib import Path
from typing import Any, Dict, List, Set

from deply.models.code_element import CodeElement
from .base_collector import BaseCollector


class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.must_configs = config.get('must', [])
        self.any_of_configs = config.get('any_of', [])
        self.must_not_configs = config.get('must_not', [])

        # Pre-instantiate sub-collectors
        from .collector_factory import CollectorFactory
        self.must_collectors = [CollectorFactory.create(c, paths, exclude_files) for c in self.must_configs]
        self.any_of_collectors = [CollectorFactory.create(c, paths, exclude_files) for c in self.any_of_configs]
        self.must_not_collectors = [CollectorFactory.create(c, paths, exclude_files) for c in self.must_not_configs]

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        must_sets = []
        for c in self.must_collectors:
            must_sets.append(c.match_in_file(file_ast, file_path))
        any_of_sets = []
        for c in self.any_of_collectors:
            any_of_sets.append(c.match_in_file(file_ast, file_path))
        must_not_elements = set()
        for c in self.must_not_collectors:
            must_not_elements.update(c.match_in_file(file_ast, file_path))

        if must_sets:
            must_elements = set.intersection(*must_sets) if must_sets else set()
        else:
            must_elements = None

        if any_of_sets:
            any_of_elements = set.union(*any_of_sets) if any_of_sets else set()
        else:
            any_of_elements = None

        if must_elements is not None and any_of_elements is not None:
            combined_elements = must_elements & any_of_elements
        elif must_elements is not None:
            combined_elements = must_elements
        elif any_of_elements is not None:
            combined_elements = any_of_elements
        else:
            combined_elements = set()

        final_elements = combined_elements - must_not_elements

        return final_elements
