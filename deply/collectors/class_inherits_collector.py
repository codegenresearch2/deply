import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name

class ClassInheritsCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.base_class = config.get("base_class", "")
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]
        self.exclude_regex = re.compile(config.get("exclude_files_regex", "")) if config.get("exclude_files_regex", "") else None
        self.paths = [Path(p) for p in paths]

    def collect(self) -> Set[CodeElement]:
        all_files = self.get_all_files()
        collected_elements = set()

        for file_path, base_path in all_files:
            tree = self.parse_file(file_path)
            if tree is None:
                continue
            classes = self.match_in_file(tree, file_path)
            collected_elements.update(classes)

        return collected_elements

    def get_all_files(self) -> List[Tuple[Path, Path]]:
        all_files = []
        for base_path in self.paths:
            if base_path.exists():
                files = [f for f in base_path.rglob("*.py") if f.is_file() and not any(pattern.search(str(f.relative_to(base_path))) for pattern in self.exclude_files) and (not self.exclude_regex or not self.exclude_regex.match(str(f.relative_to(base_path))))]
                all_files.extend([(f, base_path) for f in files])
        return all_files

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def match_in_file(self, tree, file_path: Path) -> Set[CodeElement]:
        import_aliases = get_import_aliases(tree)
        classes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = get_base_name(base, import_aliases)
                    if base_name == self.base_class or base_name.endswith(f".{self.base_class}"):
                        full_name = self._get_full_name(node)
                        code_element = CodeElement(file=file_path, name=full_name, element_type='class', line=node.lineno, column=node.col_offset)
                        classes.add(code_element)
        return classes

    def _get_full_name(self, node):
        names = []
        while isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.append(node.name)
            node = getattr(node, 'parent', None)
        return '.'.join(reversed(names))

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node