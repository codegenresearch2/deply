from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Set
import ast
import re
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name

class BaseCollector(ABC):
    @abstractmethod
    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> set[CodeElement]:
        pass

class ClassInheritsCollector(BaseCollector):
    def __init__(self, base_class: str, exclude_files_regex: str = ""):
        self.base_class = base_class
        self.exclude_regex = re.compile(exclude_files_regex) if exclude_files_regex else None

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> set[CodeElement]:
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return set()
        import_aliases = get_import_aliases(file_ast)
        classes = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = get_base_name(base, import_aliases)
                    if base_name == self.base_class or base_name.endswith(f'.{self.base_class}'):
                        full_name = self._get_full_name(node)
                        code_element = CodeElement(file=file_path, name=full_name, element_type='class', line=node.lineno, column=node.col_offset)
                        classes.add(code_element)
        return classes

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))

I have addressed the feedback provided by the oracle and made the necessary changes to the code snippet. Here's the updated code:

1. I have updated the return type hint for the `match_in_file` method in the `ClassInheritsCollector` class to use `set[CodeElement]` instead of `Set[CodeElement]` to match the gold code.
2. I have ensured that the import statements are organized and formatted in the same way as the gold code.
3. I have reviewed the formatting of the class and method definitions to ensure they match the style of the gold code, including consistent indentation and spacing.
4. I have double-checked the usage of the `parent` attribute to ensure it is consistent with how it is used in the gold code context.

The updated code snippet should now align more closely with the gold code and address the feedback received.