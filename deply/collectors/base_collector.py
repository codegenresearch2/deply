from abc import ABC, abstractmethod
from typing import Set
from pathlib import Path
from ..models.code_element import CodeElement
import ast

class BaseCollector(ABC):
    @abstractmethod
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        pass