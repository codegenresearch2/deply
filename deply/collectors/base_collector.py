from abc import ABC, abstractmethod
from typing import Set
from ..models.code_element import CodeElement

class BaseCollector(ABC):
    def __init__(self, config: dict, paths: list[str], exclude_files: list[str]):
        self.config = config
        self.paths = paths
        self.exclude_files = exclude_files
        self.exclude_regex = re.compile(self.config.get("exclude_files_regex", "")) if self.config.get("exclude_files_regex", "") else None

    def collect(self) -> Set[CodeElement]:
        elements = set()
        for path in self.paths:
            if self.exclude_regex and self.exclude_regex.search(str(path)):
                continue
            elements.update(self.match_in_file(path))
        return elements

    @abstractmethod
    def match_in_file(self, file_path: str) -> Set[CodeElement]:
        pass