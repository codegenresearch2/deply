from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Set
import ast
import re
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name

class BaseCollector(ABC):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.base_class = config.get("base_class", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None
        self.paths = paths
        self.exclude_files = exclude_files
        self.file_asts = self._load_file_asts()

    def _load_file_asts(self) -> dict:
        file_asts = {}
        for path in self.paths:
            if path in self.exclude_files or (self.exclude_regex and self.exclude_regex.search(path)):
                continue
            with open(path, 'r') as file:
                file_asts[path] = ast.parse(file.read())
        return file_asts

    @abstractmethod
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        pass

    def collect(self) -> set[CodeElement]:
        collected_elements = set()
        for file_path, file_ast in self.file_asts.items():
            collected_elements.update(self.match_in_file(file_ast, Path(file_path)))
        return collected_elements


In the rewritten code, I have added the file loading and exclusion logic to the `BaseCollector` class. This reduces file I/O operations by loading all the necessary files only once during initialization. The `match_in_file` method is left as an abstract method to be implemented by subclasses, and the `collect` method iterates over the loaded file ASTs to collect the elements. This improves code organization and readability by separating concerns and following the single responsibility principle.