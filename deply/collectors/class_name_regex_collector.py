import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name

class ClassNameRegexCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.regex_pattern = config.get("class_name_regex", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.regex = re.compile(self.regex_pattern)
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        all_files = self.get_all_files()

        for file_path, base_path in all_files:
            tree = self.parse_file(file_path)
            if tree is None:
                continue
            self.annotate_parent(tree)
            classes = self.get_matching_classes(tree, file_path)
            collected_elements.update(classes)

        return collected_elements

    def get_all_files(self) -> List[Tuple[Path, Path]]:
        all_files = []

        for base_path in self.paths:
            if not base_path.exists():
                continue

            files = [f for f in base_path.rglob("*.py") if f.is_file()]

            # Apply global and collector-specific exclude patterns
            files = [f for f in files if not self.is_excluded(f, base_path)]

            # Collect files along with their base path
            files_with_base = [(f, base_path) for f in files]
            all_files.extend(files_with_base)

        return all_files

    def is_excluded(self, file_path: Path, base_path: Path) -> bool:
        relative_path = str(file_path.relative_to(base_path))
        return any(pattern.search(relative_path) for pattern in self.exclude_files) or \
               (self.exclude_regex and self.exclude_regex.search(relative_path))

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def get_matching_classes(self, tree, file_path: Path) -> Set[CodeElement]:
        classes = set()
        import_aliases = get_import_aliases(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self.regex.match(node.name):
                    full_name = self._get_full_name(node, import_aliases)
                    code_element = CodeElement(
                        file=file_path,
                        name=full_name,
                        element_type='class',
                        line=node.lineno,
                        column=node.col_offset
                    )
                    classes.add(code_element)
        return classes

    def _get_full_name(self, node, import_aliases):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        full_name = '.'.join(reversed(names))
        return get_base_name(full_name, import_aliases)

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node