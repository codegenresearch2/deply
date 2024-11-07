import ast

from .models.code_element import CodeElement


class CodeAnalyzer:
    def __init__(self, code_elements: set[CodeElement]):
        self.code_elements = code_elements
        self._dependencies: dict[CodeElement, set[tuple[CodeElement, int]]] = {}

    def analyze(self):
        name_to_element = self._build_name_to_element_map()
        for code_element in self.code_elements:
            dependencies = self._extract_dependencies(code_element, name_to_element)
            self._dependencies[code_element] = dependencies

        return self._dependencies

    def _build_name_to_element_map(self) -> dict[str, set[CodeElement]]:
        name_to_element = {}
        for elem in self.code_elements:
            name_to_element.setdefault(elem.name, set()).add(elem)
        return name_to_element

    def _extract_dependencies(
            self,
            code_element: CodeElement,
            name_to_element: dict[str, set[CodeElement]]  # not sure if this is correct
    ) -> set[tuple[CodeElement, int]]:
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
