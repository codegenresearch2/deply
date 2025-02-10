from abc import ABC, abstractmethod
from typing import Set
from ..models.code_element import CodeElement


class BaseCollector(ABC):
    def __init__(self, config: dict, paths: list[str], exclude_files: list[str]):
        self.config = config
        self.paths = paths
        self.exclude_files = exclude_files
        self.exclude_regex = re.compile(self.config.get("exclude_files_regex", "")) if self.config.get("exclude_files_regex", "") else None

    @abstractmethod
    def collect(self) -> Set[CodeElement]:
        pass

    def should_exclude_file(self, file_path: Path) -> bool:
        return self.exclude_regex and self.exclude_regex.search(str(file_path)) is not None

    def get_full_name(self, node) -> str:
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, "parent", None)
        return ".".join(reversed(names))