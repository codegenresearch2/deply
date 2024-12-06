import ast
import re
from pathlib import Path
from typing import List, Set
from deply.collectors import BaseCollector
from deply.models.code_element import CodeElement


class ClassNameRegexCollector(BaseCollector):
    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):
        self.regex_pattern = config.get("class_name_regex", "")
        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")
        self.regex = re.compile(self.regex_pattern)
        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        if self.exclude_regex and self.exclude_regex.search(str(file_path)):
            return set()

        #self.annotate_parent(file_ast)
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

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node