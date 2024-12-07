import ast
import re
from pathlib import Path
from typing import List, Set, Dict

from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement
from deply.utils.ast_utils import get_import_aliases, get_base_name, get_decorator_name, get_annotation_name


class DirectoryCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.directories = config.get("directories", [])
        self.recursive = config.get("recursive", True)
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.element_type = config.get("element_type", "")  # 'class', 'function', 'variable'
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

        self.base_paths = [Path(p) for p in paths]
        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        # Check global exclude patterns
        if any(pattern.search(str(file_path)) for pattern in self.exclude_files):
            return set()
        # Check collector-specific exclude pattern
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return set()

        # Check if file is within one of the specified directories
        if not self.is_in_directories(file_path):
            return set()

        import_aliases = get_import_aliases(file_ast)
        elements = set()

        # Collect classes if element_type is empty or 'class'
        if not self.element_type or self.element_type == 'class':
            elements.update(self.get_classes(file_ast, file_path, import_aliases))

        # Collect functions if element_type is empty or 'function'
        if not self.element_type or self.element_type == 'function':
            elements.update(self.get_functions(file_ast, file_path, import_aliases))

        # Collect variables if element_type is empty or 'variable'
        if not self.element_type or self.element_type == 'variable':
            elements.update(self.get_variables(file_ast, file_path, import_aliases))

        return elements

    def is_in_directories(self, file_path: Path) -> bool:
        # Check if file_path is inside any of the specified directories (relative to any base_path)
        for base_path in self.base_paths:
            try:
                file_path.relative_to(base_path)
            except ValueError:
                # file_path not under base_path
                continue
            for d in self.directories:
                dir_path = base_path / d
                try:
                    # Check if relative path of file is under dir_path
                    file_path.relative_to(dir_path)
                    return True
                except ValueError:
                    pass
        return False

    def get_classes(self, tree: ast.AST, file_path: Path, import_aliases: Dict[str, str]) -> Set[CodeElement]:
        classes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                full_name = self._get_full_name(node)

                # Gather inherits
                inherits_list = []
                for base in node.bases:
                    base_name = get_base_name(base, import_aliases)
                    inherits_list.append(base_name)

                # Gather decorators
                decorators_list = []
                for d in node.decorator_list:
                    dec_name = get_decorator_name(d)
                    if dec_name is not None:
                        decorators_list.append(dec_name)

                # Gather type annotations (class-level attributes)
                type_annotations: Dict[str, str] = {}
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                        ann_name = get_annotation_name(stmt.annotation, import_aliases)
                        if ann_name is not None:
                            type_annotations[stmt.target.id] = ann_name

                code_element = CodeElement(
                    file=file_path,
                    name=full_name,
                    element_type='class',
                    line=node.lineno,
                    column=node.col_offset,
                    inherits=tuple(inherits_list),
                    decorators=tuple(decorators_list),
                    return_annotation=None,  # Classes do not have return annotations
                    type_annotations=frozenset(type_annotations.items())
                )
                classes.add(code_element)
        return classes

    def get_functions(self, tree: ast.AST, file_path: Path, import_aliases: Dict[str, str]) -> Set[CodeElement]:
        functions = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                full_name = self._get_full_name(node)

                # Decorators
                decorators_list = []
                for d in node.decorator_list:
                    dec_name = get_decorator_name(d)
                    if dec_name is not None:
                        decorators_list.append(dec_name)

                # Return annotation
                if getattr(node, 'returns', None):
                    return_annotation = get_annotation_name(node.returns, import_aliases)
                else:
                    return_annotation = None

                # Parameter type annotations
                type_ann_map: Dict[str, str] = {}
                # Positional args
                for arg in node.args.args:
                    if arg.annotation is not None:
                        ann_name = get_annotation_name(arg.annotation, import_aliases)
                        if ann_name is not None:
                            type_ann_map[arg.arg] = ann_name
                # Kw-only args
                for arg in node.args.kwonlyargs:
                    if arg.annotation is not None:
                        ann_name = get_annotation_name(arg.annotation, import_aliases)
                        if ann_name is not None:
                            type_ann_map[arg.arg] = ann_name
                # Pos-only args
                if hasattr(node.args, 'posonlyargs'):
                    for arg in node.args.posonlyargs:
                        if arg.annotation is not None:
                            ann_name = get_annotation_name(arg.annotation, import_aliases)
                            if ann_name is not None:
                                type_ann_map[arg.arg] = ann_name
                # Vararg and kwarg
                if node.args.vararg and node.args.vararg.annotation:
                    ann_name = get_annotation_name(node.args.vararg.annotation, import_aliases)
                    if ann_name is not None:
                        type_ann_map[node.args.vararg.arg] = ann_name
                if node.args.kwarg and node.args.kwarg.annotation:
                    ann_name = get_annotation_name(node.args.kwarg.annotation, import_aliases)
                    if ann_name is not None:
                        type_ann_map[node.args.kwarg.arg] = ann_name

                # Functions do not inherit
                inherits_list = []

                code_element = CodeElement(
                    file=file_path,
                    name=full_name,
                    element_type='function',
                    line=node.lineno,
                    column=node.col_offset,
                    inherits=tuple(inherits_list),
                    decorators=tuple(decorators_list),
                    return_annotation=return_annotation,
                    type_annotations=frozenset(type_ann_map.items())
                )
                functions.add(code_element)
        return functions

    def get_variables(self, tree: ast.AST, file_path: Path, import_aliases: Dict[str, str]) -> Set[CodeElement]:
        variables = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                # Variables with annotations
                ann_name = get_annotation_name(node.annotation, import_aliases)
                type_ann_map = {node.target.id: ann_name} if ann_name else {}
                code_element = CodeElement(
                    file=file_path,
                    name=node.target.id,
                    element_type='variable',
                    line=node.target.lineno,
                    column=node.target.col_offset,
                    inherits=tuple(),
                    decorators=tuple(),
                    return_annotation=None,
                    type_annotations=frozenset(type_ann_map.items())
                )
                variables.add(code_element)
            elif isinstance(node, ast.Assign):
                # Variables without annotations
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        code_element = CodeElement(
                            file=file_path,
                            name=target.id,
                            element_type='variable',
                            line=target.lineno,
                            column=target.col_offset,
                            inherits=tuple(),
                            decorators=tuple(),
                            return_annotation=None,
                            type_annotations=frozenset()
                        )
                        variables.add(code_element)
        return variables

    def _get_full_name(self, node: ast.AST) -> str:
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(current.name)
            current = getattr(current, 'parent', None)
        return '.'.join(reversed(names))
