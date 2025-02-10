import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name

class DirectoryCollector(BaseCollector):
    def __init__(self, config: dict, base_paths: List[str], exclude_files: List[str]):
        self.directories = config.get("directories", [])
        self.recursive = config.get("recursive", True)
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.element_type = config.get("element_type", "")  # 'class', 'function', 'variable'

        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.base_paths = [Path(p) for p in base_paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def collect(self) -> Set[CodeElement]:
        collected_elements = set()
        all_files = self.get_all_files()

        for file_path in all_files:
            elements = self.match_in_file(file_path)
            collected_elements.update(elements)

        return collected_elements

    def get_all_files(self) -> List[Path]:
        all_files = []

        for base_path in self.base_paths:
            if not base_path.exists():
                continue

            if self.recursive:
                files = [f for f in base_path.rglob('*.py') if f.is_file() and self.is_in_directories(f, base_path)]
            else:
                files = [f for f in base_path.glob('*.py') if f.is_file() and self.is_in_directories(f, base_path)]

            # Apply global exclude patterns
            files = [f for f in files if not any(pattern.search(str(f.relative_to(base_path))) for pattern in self.exclude_files)]

            # Apply collector-specific exclude pattern
            if self.exclude_regex:
                files = [f for f in files if not self.exclude_regex.match(str(f.relative_to(base_path)))]

            all_files.extend(files)

        return all_files

    def is_in_directories(self, file_path: Path, base_path: Path) -> bool:
        relative_path = file_path.relative_to(base_path)
        return any(relative_path.parts[0] == directory for directory in self.directories)

    def match_in_file(self, file_path: Path) -> Set[CodeElement]:
        elements = set()
        tree = self.parse_file(file_path)
        if tree is None:
            return elements

        self.annotate_parent(tree)

        if not self.element_type or self.element_type == 'class':
            elements.update(self.get_class_names(tree, file_path))

        if not self.element_type or self.element_type == 'function':
            elements.update(self.get_function_names(tree, file_path))

        if not self.element_type or self.element_type == 'variable':
            elements.update(self.get_variable_names(tree, file_path))

        return elements

    def parse_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def get_class_names(self, tree, file_path: Path) -> Set[CodeElement]:
        classes = set()
        import_aliases = get_import_aliases(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                full_name = self._get_full_name(node)
                code_element = CodeElement(
                    file=file_path,
                    name=full_name,
                    element_type='class',
                    line=node.lineno,
                    column=node.col_offset
                )
                classes.add(code_element)

                # Add base classes to the set
                for base in node.bases:
                    base_name = get_base_name(base, import_aliases)
                    base_code_element = CodeElement(
                        file=file_path,
                        name=base_name,
                        element_type='class',
                        line=node.lineno,
                        column=node.col_offset
                    )
                    classes.add(base_code_element)
        return classes

    def get_function_names(self, tree, file_path: Path) -> Set[CodeElement]:
        functions = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                full_name = self._get_full_name(node)
                code_element = CodeElement(
                    file=file_path,
                    name=full_name,
                    element_type='function',
                    line=node.lineno,
                    column=node.col_offset
                )
                functions.add(code_element)
        return functions

    def get_variable_names(self, tree, file_path: Path) -> Set[CodeElement]:
        variables = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        code_element = CodeElement(
                            file=file_path,
                            name=target.id,
                            element_type='variable',
                            line=target.lineno,
                            column=target.col_offset
                        )
                        variables.add(code_element)
        return variables

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node