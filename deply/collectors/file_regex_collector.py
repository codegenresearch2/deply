import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement


class BoolCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.regex_pattern = config.get('bool_regex', '')
        self.exclude_files_regex_pattern = config.get('exclude_files_regex', '')
        self.regex = re.compile(self.regex_pattern)
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return set()

        classes = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.ClassDef):
                if self.regex.match(node.name):
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

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))


class FileRegexCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.regex_pattern = config.get('regex', '')
        self.exclude_files_regex_pattern = config.get('exclude_files_regex', '')
        self.element_type = config.get('element_type', '')
        self.regex = re.compile(self.regex_pattern)
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None
        self.paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return set()

        elements = set()
        if self.element_type:
            if self.element_type == 'class':
                elements.update(self._collect_class_elements(file_ast, file_path))
            elif self.element_type == 'function':
                elements.update(self._collect_function_elements(file_ast, file_path))
            elif self.element_type == 'variable':
                elements.update(self._collect_variable_elements(file_ast, file_path))
        else:
            elements.update(self._collect_class_elements(file_ast, file_path))
            elements.update(self._collect_function_elements(file_ast, file_path))
            elements.update(self._collect_variable_elements(file_ast, file_path))
        return elements

    def _collect_class_elements(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        classes = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.ClassDef):
                if self.regex.match(node.name):
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

    def _collect_function_elements(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        functions = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.FunctionDef):
                if self.regex.match(node.name):
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

    def _collect_variable_elements(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        variables = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if self.regex.match(target.id):
                            code_element = CodeElement(
                                file=file_path,
                                name=target.id,
                                element_type='variable',
                                line=target.lineno,
                                column=target.col_offset
                            )
                            variables.add(code_element)
        return variables

    def get_all_files(self) -> List[Tuple[Path, Path]]:
        all_files = []
        for base_path in self.paths:
            if not base_path.exists():
                continue
            files = [f for f in base_path.rglob('*.py') if f.is_file()]
            files = [f for f in files if not any(pattern.search(str(f.relative_to(base_path))) for pattern in self.exclude_files)]
            if self.exclude_regex:
                files = [f for f in files if not self.exclude_regex.match(str(f.relative_to(base_path)))]
            all_files.extend([(f, base_path) for f in files])
        return all_files

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))
