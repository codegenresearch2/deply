from abc import ABC, abstractmethod
from pathlib import Path
from typing import Set
import ast
from deply.models.code_element import CodeElement

class BaseCollector(ABC):
    @abstractmethod
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        pass

class BoolCollector(BaseCollector):
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        # Implementation for BoolCollector
        pass

class ClassInheritsCollector(BaseCollector):
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        # Implementation for ClassInheritsCollector
        pass

class ClassNameRegexCollector(BaseCollector):
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        # Implementation for ClassNameRegexCollector
        pass

class DecoratorUsageCollector(BaseCollector):
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        # Implementation for DecoratorUsageCollector
        pass

class DirectoryCollector(BaseCollector):
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        # Implementation for DirectoryCollector
        pass

class FileRegexCollector(BaseCollector):
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        # Implementation for FileRegexCollector
        pass