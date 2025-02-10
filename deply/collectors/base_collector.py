import ast
from pathlib import Path
from typing import Set
from ..models.code_element import CodeElement

class BaseCollector(ABC):
    @abstractmethod
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        pass