from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Set
import ast
import re
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name

class BaseCollector(ABC):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None
        self.paths = paths

    @abstractmethod
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        pass

    def collect(self) -> set[CodeElement]:
        collected_elements = set()
        for path in self.paths:
            for file_path in Path(path).rglob('*.py'):
                if self.exclude_regex and self.exclude_regex.search(str(file_path)):
                    continue
                with open(file_path, 'r') as file:
                    file_ast = ast.parse(file.read())
                    collected_elements.update(self.match_in_file(file_ast, file_path))
        return collected_elements


In the rewritten code, I have added the initialization of `exclude_regex` and `paths` to the `BaseCollector` class. I have also moved the file collection and exclusion logic to the `collect` method. This method iterates over the provided paths, checks for exclusion patterns, and calls the `match_in_file` method for each Python file. The `match_in_file` method is left as an abstract method to be implemented by subclasses.