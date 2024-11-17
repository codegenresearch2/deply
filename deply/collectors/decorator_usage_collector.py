import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement


class DecoratorUsageCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.decorator_name = config.get("decorator_name", "")
        self.decorator_regex_pattern = config.get("decorator_regex", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.decorator_regex = re.compile(self.decorator_regex_pattern) if self.decorator_regex_pattern else None
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
            elements = self.get_elements_with_decorator(tree, file_path)
            collected_elements.update(elements)

        return collected_elements

    def get_all_files(self) -> List[Tuple[Path, Path]]:
        all_files = []

        for base_path in self.paths:
            if not base_path.exists():
                continue

            files = [f for f in base_path.rglob('*.py') if f.is_file()]

            # Apply global exclude patterns
            def is_excluded(file_path: Path) -> bool:
                relative_path = str(file_path.relative_to(base_path))
                return any(pattern.search(relative_path) for pattern in self.exclude_files)

            files = [f for f in files if not is_excluded(f)]

            # Apply collector-specific exclude pattern
            if self.exclude_regex:
                files = [
                    f for f in files
                    if not self.exclude_regex.match(str(f.relative_to(base_path)))
                ]

            # Collect files along with their base path
            files_with_base = [(f, base_path) for f in files]
            all_files.extend(files_with_base)

        return all_files

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def get_elements_with_decorator(self, tree, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    decorator_name = self._get_full_name(decorator)
                    if self.decorator_name and decorator_name == self.decorator_name:
                        full_name = self._get_full_name(node)
                        code_element = CodeElement(
                            file=file_path,
                            name=full_name,
                            element_type='function' if isinstance(node,
                                                                  (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class',
                            line=node.lineno,
                            column=node.col_offset
                        )
                        elements.add(code_element)
                    elif self.decorator_regex and self.decorator_regex.match(decorator_name):
                        full_name = self._get_full_name(node)
                        code_element = CodeElement(
                            file=file_path,
                            name=full_name,
                            element_type='function' if isinstance(node,
                                                                  (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class',
                            line=node.lineno,
                            column=node.col_offset
                        )
                        elements.add(code_element)
        return elements

    def _get_full_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_full_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            else:
                return node.attr
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names = []
            current = node
            while isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(current.name)
                current = getattr(current, 'parent', None)
            return '.'.join(reversed(names))
        elif isinstance(node, ast.Call):
            return self._get_full_name(node.func)
        else:
            return ''

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
