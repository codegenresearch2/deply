import ast
import re
from pathlib import Path
from typing import List, Set

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name

class ClassInheritsCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.base_class = config.get("base_class", "")
        self.exclude_regex = re.compile(config.get("exclude_files_regex", "")) if config.get("exclude_files_regex", "") else None
        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        for base_path in self.paths:
            if base_path.exists():
                for file_path in base_path.rglob("*.py"):
                    if not any(pattern.search(str(file_path.relative_to(base_path))) for pattern in self.exclude_files) and not (self.exclude_regex and self.exclude_regex.search(str(file_path.relative_to(base_path)))):
                        tree = self.parse_file(file_path)
                        if tree is not None:
                            classes = self.match_in_file(tree, file_path)
                            collected_elements.update(classes)
        return collected_elements

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
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