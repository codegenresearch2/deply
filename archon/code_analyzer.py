import ast
from typing import Dict, Set, Tuple

from .models.code_element import CodeElement


class CodeAnalyzer:
    def __init__(self, code_elements: Set[CodeElement]):
        self.code_elements = code_elements
        self.dependencies = {}  # Dict[CodeElement, Set[Tuple[CodeElement, int]]]

    def analyze(self):
        name_to_element = self._build_name_to_element_map()
        for code_element in self.code_elements:
            dependencies = self._extract_dependencies(code_element, name_to_element)
            self.dependencies[code_element] = dependencies

    def _build_name_to_element_map(self) -> Dict[str, Set[CodeElement]]:
        name_to_element = {}
        for elem in self.code_elements:
            name_to_element.setdefault(elem.name, set()).add(elem)
        return name_to_element

    def _extract_dependencies(self, code_element: CodeElement, name_to_element: Dict[str, Set[CodeElement]]) -> Set[
        Tuple[CodeElement, int]]:
        dependencies = set()
        with open(code_element.file, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=str(code_element.file))
            except SyntaxError:
                return dependencies  # Skip files with syntax errors

        class DependencyVisitor(ast.NodeVisitor):
            def __init__(self, dependencies):
                self.dependencies = dependencies

            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        self.dependencies.add((dep_element, node.lineno))

            def visit_ImportFrom(self, node):
                module = node.module
                for alias in node.names:
                    name = alias.asname or alias.name
                    full_name = f"{module}.{name}" if module else name
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        self.dependencies.add((dep_element, node.lineno))

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        self.dependencies.add((dep_element, node.lineno))
                self.generic_visit(node)

            def visit_Attribute(self, node):
                if isinstance(node.value, ast.Name):
                    name = f"{node.value.id}.{node.attr}"
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        self.dependencies.add((dep_element, node.lineno))
                self.generic_visit(node)

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    name = node.id
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        self.dependencies.add((dep_element, node.lineno))

        visitor = DependencyVisitor(dependencies)
        visitor.visit(tree)
        return dependencies
