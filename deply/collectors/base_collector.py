from abc import ABC, abstractmethod
from typing import Set
from ..models.code_element import CodeElement


class BaseCollector(ABC):
    def __init__(self, config: dict, paths: list[str], exclude_files: list[str]):
        self.config = config
        self.paths = paths
        self.exclude_files = exclude_files

    def collect(self) -> Set[CodeElement]:
        elements = set()
        for path in self.paths:
            if self._should_process_file(path):
                elements.update(self._collect_from_file(path))
        return elements

    def _should_process_file(self, file_path: str) -> bool:
        return not any(re.match(pattern, file_path) for pattern in self.exclude_files)

    @abstractmethod
    def _collect_from_file(self, file_path: str) -> Set[CodeElement]:
        pass