import ast
import re
from pathlib import Path
from typing import List, Set, Tuple
from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement

class DirectoryCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.directories = config.get("directories", [])
        self.recursive = config.get("recursive", True)
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.element_type = config.get("element_type", "")  # 'class', 'function', 'variable'

        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.base_paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def match_in_file(self, file_path: Path) -> Set[CodeElement]:
        if self.is_excluded(file_path):
            return set()

        elements = set()
        tree = self.parse_file(file_path)
        if tree is None:
            return elements

        if not self.element_type or self.element_type == 'class':
            elements.update(self.get_class_names(tree, file_path))

        if not self.element_type or self.element_type == 'function':
            elements.update(self.get_function_names(tree, file_path))

        if not self.element_type or self.element_type == 'variable':
            elements.update(self.get_variable_names(tree, file_path))

        return elements

    def is_excluded(self, file_path: Path) -> bool:
        relative_path = str(file_path.relative_to(self.base_paths[0]))
        return any(pattern.search(relative_path) for pattern in self.exclude_files) or \
               (self.exclude_regex and self.exclude_regex.search(str(file_path)))

    def get_all_files(self) -> List[Tuple[Path, Path]]:
        all_files = []

        for base_path in self.base_paths:
            if not base_path.exists():
                continue

            # Collect files only in specified directories
            for directory in self.directories:
                dir_path = base_path / directory
                if dir_path.exists() and dir_path.is_dir():
                    if self.recursive:
                        files = [f for f in dir_path.rglob('*.py') if f.is_file()]
                    else:
                        files = [f for f in dir_path.glob('*.py') if f.is_file()]

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

    def get_class_names(self, tree, file_path: Path) -> Set[CodeElement]:
        # self.annotate_parent(tree)  # Commented out as per oracle feedback
        classes = set()
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
        return classes

    def get_function_names(self, tree, file_path: Path) -> Set[CodeElement]:
        # self.annotate_parent(tree)  # Commented out as per oracle feedback
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