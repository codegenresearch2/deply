import ast
import re
from pathlib import Path
from typing import List, Set
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

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        all_files = self.get_all_files()

        for file_path in all_files:
            tree = self.parse_file(file_path)
            if tree is None or self.exclude_regex and self.exclude_regex.search(str(file_path)):
                continue
            elements = self.match_in_file(tree, file_path)
            collected_elements.update(elements)

        return collected_elements

    def get_all_files(self) -> List[Path]:
        all_files = []

        for base_path in self.paths:
            if not base_path.exists():
                continue

            files = [f for f in base_path.rglob('*.py') if f.is_file()]

            # Apply global exclude pattern
            if self.exclude_regex:
                files = [f for f in files if not self.exclude_regex.search(str(f.relative_to(base_path)))]

            all_files.extend(files)

        return all_files

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def match_in_file(self, tree, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    d_name = self._get_decorator_name(decorator)
                    if self.decorator_name == d_name or (self.decorator_regex and self.decorator_regex.match(d_name)):
                        full_name = self._get_full_name(node)
                        code_element = CodeElement(
                            file=file_path,
                            name=full_name,
                            element_type='class' if isinstance(node, ast.ClassDef) else 'function',
                            line=node.lineno,
                            column=node.col_offset
                        )
                        elements.add(code_element)
        return elements

    def _get_decorator_name(self, decorator):
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        else:
            return ''

    def _get_full_name(self, node):
        names = []
        current = node
        while current:
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node