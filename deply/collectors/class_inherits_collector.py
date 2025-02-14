import ast
import re
from pathlib import Path
from typing import List, Set

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name
from deply.collectors.directory_collector import DirectoryCollector

class ClassInheritsCollector(DirectoryCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        super().__init__(config, paths, exclude_files)
        self.base_class = config.get("base_class", "")

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        if not super().match_in_file(file_ast, file_path):  # apply base class filtering
            return set()
        return self.get_classes_inheriting(file_ast, file_path)

    def get_classes_inheriting(self, tree, file_path: Path) -> Set[CodeElement]:
        import_aliases = get_import_aliases(tree)
        classes = set()
        for node in ast.iter_child_nodes(tree):  # only iterate over direct children to reduce redundant operations
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = get_base_name(base, import_aliases)
                    if base_name == self.base_class or base_name.endswith(f".{self.base_class}"):
                        full_name = self._get_full_name(node)
                        code_element = CodeElement(
                            file=file_path,
                            name=full_name,
                            element_type='class',
                            line=node.lineno,
                            column=node.col_offset
                        )
                        classes.add(code_element)
        return classes


The code has been refactored to improve readability, reduce redundant operations, and create more flexible and reusable components. The `ClassInheritsCollector` now inherits from `DirectoryCollector`, which provides common functionalities for filtering files based on paths and exclusion patterns. This promotes code reuse. The `get_classes_inheriting` method has been updated to iterate over direct child nodes of the tree, reducing unnecessary iterations.