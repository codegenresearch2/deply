from abc import ABC, abstractmethod
from typing import Set
from ..models.code_element import CodeElement


class BaseCollector(ABC):
    def __init__(self, config: dict, paths: list[str], exclude_files: list[str]):
        self.config = config
        self.paths = paths
        self.exclude_files = exclude_files
        self.exclude_regex = self._compile_exclude_regex()

    def _compile_exclude_regex(self) -> re.Pattern:
        exclude_files_regex_pattern = self.config.get("exclude_files_regex", "")
        return re.compile(exclude_files_regex_pattern) if exclude_files_regex_pattern else None

    @abstractmethod
    def collect(self) -> Set[CodeElement]:
        pass