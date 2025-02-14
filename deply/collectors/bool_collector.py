import ast
from typing import Any, Dict, List, Set
from pathlib import Path

from deply.models.code_element import CodeElement
from .base_collector import BaseCollector
from .collector_factory import CollectorFactory

class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.paths = [Path(p) for p in paths]
        self.exclude_files = [Path(f) for f in exclude_files]
        self.must_configs = config.get('must', [])
        self.any_of_configs = config.get('any_of', [])
        self.must_not_configs = config.get('must_not', [])

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        must_sets = [self.collect_elements(self.must_configs, file_ast, file_path)]
        any_of_sets = [self.collect_elements(self.any_of_configs, file_ast, file_path)]
        must_not_elements = self.collect_elements(self.must_not_configs, file_ast, file_path)

        must_elements = set.intersection(*must_sets) if must_sets else set()
        any_of_elements = set.union(*any_of_sets) if any_of_sets else set()

        if must_elements and any_of_elements:
            combined_elements = must_elements & any_of_elements
        else:
            combined_elements = must_elements or any_of_elements

        final_elements = combined_elements - must_not_elements

        return final_elements

    def collect_elements(self, configs: List[Dict[str, Any]], file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for collector_config in configs:
            collector = CollectorFactory.create(collector_config, [str(file_path)], [str(file_path)])
            elements.update(collector.match_in_file(file_ast, file_path))
        return elements

    def collect(self) -> Set[CodeElement]:
        elements = set()
        for path in self.paths:
            if path.is_file() and path not in self.exclude_files:
                with open(path, 'r') as file:
                    file_ast = ast.parse(file.read())
                    elements.update(self.match_in_file(file_ast, path))
            elif path.is_dir() and path not in self.exclude_files:
                for file_path in path.rglob('*'):
                    if file_path.is_file() and file_path not in self.exclude_files:
                        with open(file_path, 'r') as file:
                            file_ast = ast.parse(file.read())
                            elements.update(self.match_in_file(file_ast, file_path))
        return elements


The provided code snippet has been rewritten to enhance code organization and clarity, improve file collection and exclusion logic, and utilize AST for code analysis efficiently. I have made the following changes:

1. Imported the `Path` class from the `pathlib` module to handle file and directory paths.
2. Converted the `paths` and `exclude_files` lists to `Path` objects for easier file and directory operations.
3. Implemented the `match_in_file` method to collect code elements based on the provided configuration and AST of a single file.
4. Created the `collect_elements` method to collect code elements for a given list of collector configurations, file AST, and file path.
5. Updated the `collect` method to handle both files and directories, and excluded files specified in the `exclude_files` list.
6. Utilized the `rglob` method to recursively search for files in directories.
7. Parsed the file content using the `ast.parse` method to obtain the AST.
8. Called the `match_in_file` method to collect code elements for each file.
9. Returned the collected code elements as a set.