from abc import ABC, abstractmethod
from typing import Set
from pathlib import Path
import ast

from ..models.code_element import CodeElement


class BaseCollector(ABC):
    @abstractmethod
    def collect(self) -> Set[CodeElement]:
        pass

    @abstractmethod
    def _collect_from_file(self, file_path: Path, file_ast: ast.AST) -> Set[CodeElement]:
        pass


class ClassInheritsCollector(BaseCollector):
    def __init__(self, config: dict, paths: list[str], exclude_files: list[str]):
        self.config = config
        self.paths = paths
        self.exclude_files = exclude_files
        self.base_class = config.get("base_class", "")
        self.exclude_regex = re.compile(config.get("exclude_files_regex", "")) if config.get("exclude_files_regex", "") else None

    def collect(self) -> Set[CodeElement]:
        elements = set()
        for path in self.paths:
            if self._should_process_file(path):
                elements.update(self._collect_from_file(Path(path), self._parse_file(Path(path))))
        return elements

    def _should_process_file(self, file_path: str) -> bool:
        return not any(re.match(pattern, file_path) for pattern in self.exclude_files)

    def _parse_file(self, file_path: Path) -> ast.AST:
        with open(file_path, "r") as file:
            return ast.parse(file.read(), filename=str(file_path))

    def _collect_from_file(self, file_path: Path, file_ast: ast.AST) -> Set[CodeElement]:
        import_aliases = get_import_aliases(file_ast)
        classes = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = get_base_name(base, import_aliases)
                    if base_name == self.base_class or base_name.endswith(f".{self.base_class}"):
                        full_name = self._get_full_name(node)
                        code_element = CodeElement(file=file_path, name=full_name, element_type="class", line=node.lineno, column=node.col_offset)
                        classes.add(code_element)
        return classes

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, "parent", None)
        return "".join(reversed(names))
