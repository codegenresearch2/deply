import ast

from .models.code_element import CodeElement
from .models.dependency import Dependency


class CodeAnalyzer:
    def __init__(self, code_elements: set[CodeElement]):
        self.code_elements = code_elements
        self._dependencies: set[Dependency] = set()

    def analyze(self) -> set[Dependency]:
        name_to_elements = self._build_name_to_element_map()
        for code_element in self.code_elements:
            dependencies = self._extract_dependencies(code_element, name_to_elements)
            self._dependencies.update(dependencies)
        return self._dependencies

    def _build_name_to_element_map(self) -> dict[str, set[CodeElement]]:
        name_to_element = {}
        for elem in self.code_elements:
            name_to_element.setdefault(elem.name, set()).add(elem)
        return name_to_element

    def _extract_dependencies(
            self,
            code_element: CodeElement,
            name_to_element: dict[str, set[CodeElement]]
    ) -> set[Dependency]:
        dependencies = set()
        try:
            with open(code_element.file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(code_element.file))
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return dependencies  # Skip files with syntax errors or access issues

        class DependencyVisitor(ast.NodeVisitor):
            def __init__(self, dependencies: set[Dependency], source: CodeElement):
                self.dependencies = dependencies
                self.source = source

            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        dependency = Dependency(
                            code_element=self.source,
                            depends_on_code_element=dep_element,
                            # dependency_type='import',
                            line=node.lineno,
                            column=node.col_offset
                        )
                        self.dependencies.add(dependency)

            def visit_ImportFrom(self, node):
                module = node.module
                for alias in node.names:
                    name = alias.asname or alias.name
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        dependency = Dependency(
                            code_element=self.source,
                            depends_on_code_element=dep_element,
                            # dependency_type='import_from',
                            line=node.lineno,
                            column=node.col_offset
                        )
                        self.dependencies.add(dependency)

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        dependency = Dependency(
                            code_element=self.source,
                            depends_on_code_element=dep_element,
                            # dependency_type='function_call',
                            line=node.lineno,
                            column=node.col_offset
                        )
                        self.dependencies.add(dependency)
                self.generic_visit(node)

            def visit_Attribute(self, node):
                if isinstance(node.value, ast.Name):
                    name = f"{node.value.id}.{node.attr}"
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        dependency = Dependency(
                            code_element=self.source,
                            depends_on_code_element=dep_element,
                            # dependency_type='attribute_access',
                            line=node.lineno,
                            column=node.col_offset
                        )
                        self.dependencies.add(dependency)
                self.generic_visit(node)

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    name = node.id
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        dependency = Dependency(
                            code_element=self.source,
                            depends_on_code_element=dep_element,
                            # dependency_type='name_load',
                            line=node.lineno,
                            column=node.col_offset
                        )
                        self.dependencies.add(dependency)

        visitor = DependencyVisitor(dependencies, code_element)
        visitor.visit(tree)
        return dependencies
