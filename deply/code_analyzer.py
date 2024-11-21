import ast
import logging
from typing import Dict, Set, List

from deply.models.code_element import CodeElement
from deply.models.dependency import Dependency


class CodeAnalyzer:
    def __init__(self, code_elements: Set[CodeElement], dependency_types: List[str] = None):
        self.code_elements = code_elements
        self.dependency_types = dependency_types or [
            'import',
            'import_from',
            'function_call',
            'class_inheritance',
            'decorator',
            'type_annotation',
            'exception_handling',
            'metaclass',
            'attribute_access',
            'name_load',
        ]
        self._dependencies: Set[Dependency] = set()
        logging.debug(f"Initialized CodeAnalyzer with {len(self.code_elements)} code elements.")

    def analyze(self) -> Set[Dependency]:
        logging.debug("Starting analysis of code elements.")
        name_to_elements = self._build_name_to_element_map()
        logging.debug(f"Name to elements map built with {len(name_to_elements)} names.")
        for code_element in self.code_elements:
            logging.debug(f"Analyzing code element: {code_element.name} in file {code_element.file}")
            dependencies = self._extract_dependencies(code_element, name_to_elements)
            logging.debug(f"Found {len(dependencies)} dependencies for {code_element.name}")
            self._dependencies.update(dependencies)
        logging.debug("Completed analysis of code elements.")
        return self._dependencies

    def _build_name_to_element_map(self) -> Dict[str, Set[CodeElement]]:
        logging.debug("Building name to element map.")
        name_to_element = {}
        for elem in self.code_elements:
            name_to_element.setdefault(elem.name, set()).add(elem)
        logging.debug(f"Name to element map contains {len(name_to_element)} entries.")
        return name_to_element

    def _extract_dependencies(
            self,
            code_element: CodeElement,
            name_to_element: Dict[str, Set[CodeElement]]
    ) -> Set[Dependency]:
        logging.debug(f"Extracting dependencies for {code_element.name} in file {code_element.file}")
        dependencies = set()
        try:
            with open(code_element.file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            logging.debug(f"File {code_element.file} read successfully.")
            tree = ast.parse(source_code, filename=str(code_element.file))
            logging.debug(f"AST parsing completed for {code_element.file}.")
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError) as e:
            logging.warning(f"Failed to parse {code_element.file}: {e}")
            return dependencies  # Skip files with syntax errors or access issues

        class DependencyVisitor(ast.NodeVisitor):
            def __init__(self, dependencies: Set[Dependency], source: CodeElement, dependency_types: List[str]):
                self.dependencies = dependencies
                self.source = source
                self.dependency_types = dependency_types
                logging.debug(f"DependencyVisitor created for {self.source.name}")

            def _get_full_name(self, node):
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    value = self._get_full_name(node.value)
                    if value:
                        return f"{value}.{node.attr}"
                    else:
                        return node.attr
                elif isinstance(node, ast.Call):
                    return self._get_full_name(node.func)
                elif isinstance(node, ast.Subscript):
                    return self._get_full_name(node.value)
                elif isinstance(node, ast.Index):
                    return self._get_full_name(node.value)
                elif isinstance(node, ast.Constant):
                    return str(node.value)
                else:
                    return None

            def visit_Import(self, node):
                logging.debug(f"Visiting Import node at line {node.lineno}")
                if 'import' in self.dependency_types:
                    for alias in node.names:
                        name = alias.asname or alias.name.split('.')[0]
                        dep_elements = name_to_element.get(name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.source,
                                depends_on_code_element=dep_element,
                                dependency_type='import',
                                line=node.lineno,
                                column=node.col_offset
                            )
                            self.dependencies.add(dependency)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                logging.debug(f"Visiting ImportFrom node at line {node.lineno}")
                if 'import_from' in self.dependency_types:
                    module = node.module
                    for alias in node.names:
                        name = alias.asname or alias.name
                        dep_elements = name_to_element.get(name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.source,
                                depends_on_code_element=dep_element,
                                dependency_type='import_from',
                                line=node.lineno,
                                column=node.col_offset
                            )
                            self.dependencies.add(dependency)
                self.generic_visit(node)

            def visit_Call(self, node):
                logging.debug(f"Visiting Call node at line {node.lineno}")
                if 'function_call' in self.dependency_types:
                    if isinstance(node.func, ast.Name):
                        name = node.func.id
                        dep_elements = name_to_element.get(name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.source,
                                depends_on_code_element=dep_element,
                                dependency_type='function_call',
                                line=node.lineno,
                                column=node.col_offset
                            )
                            self.dependencies.add(dependency)
                    elif isinstance(node.func, ast.Attribute):
                        full_name = self._get_full_name(node.func)
                        dep_elements = name_to_element.get(full_name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.source,
                                depends_on_code_element=dep_element,
                                dependency_type='function_call',
                                line=node.lineno,
                                column=node.col_offset
                            )
                            self.dependencies.add(dependency)
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                logging.debug(f"Visiting ClassDef node: {node.name} at line {node.lineno}")
                if 'class_inheritance' in self.dependency_types:
                    for base in node.bases:
                        base_name = self._get_full_name(base)
                        dep_elements = name_to_element.get(base_name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.source,
                                depends_on_code_element=dep_element,
                                dependency_type='class_inheritance',
                                line=base.lineno,
                                column=base.col_offset
                            )
                            self.dependencies.add(dependency)
                if 'decorator' in self.dependency_types:
                    self._process_decorators(node)
                if 'metaclass' in self.dependency_types:
                    for keyword in node.keywords:
                        if keyword.arg == 'metaclass':
                            metaclass_name = self._get_full_name(keyword.value)
                            dep_elements = name_to_element.get(metaclass_name, set())
                            for dep_element in dep_elements:
                                dependency = Dependency(
                                    code_element=self.source,
                                    depends_on_code_element=dep_element,
                                    dependency_type='metaclass',
                                    line=keyword.value.lineno,
                                    column=keyword.value.col_offset
                                )
                                self.dependencies.add(dependency)
                self.generic_visit(node)

            def _process_decorators(self, node):
                for decorator in node.decorator_list:
                    logging.debug(f"Processing decorator at line {decorator.lineno}")
                    decorator_name = self._get_full_name(decorator)
                    dep_elements = name_to_element.get(decorator_name, set())
                    for dep_element in dep_elements:
                        dependency = Dependency(
                            code_element=self.source,
                            depends_on_code_element=dep_element,
                            dependency_type='decorator',
                            line=decorator.lineno,
                            column=decorator.col_offset
                        )
                        self.dependencies.add(dependency)

            def visit_FunctionDef(self, node):
                logging.debug(f"Visiting FunctionDef node: {node.name} at line {node.lineno}")
                if 'decorator' in self.dependency_types:
                    self._process_decorators(node)
                if 'type_annotation' in self.dependency_types:
                    # Process return type annotation
                    if node.returns:
                        self._process_annotation(node.returns)
                    # Process parameter type annotations
                    for arg in node.args.args + node.args.kwonlyargs:
                        if arg.annotation:
                            self._process_annotation(arg.annotation)
                self.generic_visit(node)

            def _process_annotation(self, annotation):
                logging.debug(f"Processing annotation at line {getattr(annotation, 'lineno', 'unknown')}")
                annotation_name = self._get_full_name(annotation)
                dep_elements = name_to_element.get(annotation_name, set())
                for dep_element in dep_elements:
                    dependency = Dependency(
                        code_element=self.source,
                        depends_on_code_element=dep_element,
                        dependency_type='type_annotation',
                        line=getattr(annotation, 'lineno', 0),
                        column=getattr(annotation, 'col_offset', 0)
                    )
                    self.dependencies.add(dependency)

            def visit_ExceptHandler(self, node):
                logging.debug(f"Visiting ExceptHandler node at line {node.lineno}")
                if 'exception_handling' in self.dependency_types:
                    if node.type:
                        exception_name = self._get_full_name(node.type)
                        dep_elements = name_to_element.get(exception_name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.source,
                                depends_on_code_element=dep_element,
                                dependency_type='exception_handling',
                                line=node.lineno,
                                column=node.col_offset
                            )
                            self.dependencies.add(dependency)
                self.generic_visit(node)

            def visit_With(self, node):
                logging.debug(f"Visiting With node at line {node.lineno}")
                if 'context_manager' in self.dependency_types:
                    for item in node.items:
                        context_expr = item.context_expr
                        context_name = self._get_full_name(context_expr)
                        dep_elements = name_to_element.get(context_name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.source,
                                depends_on_code_element=dep_element,
                                dependency_type='context_manager',
                                line=context_expr.lineno,
                                column=context_expr.col_offset
                            )
                            self.dependencies.add(dependency)
                self.generic_visit(node)

            def visit_Attribute(self, node):
                logging.debug(f"Visiting Attribute node at line {node.lineno}")
                if 'attribute_access' in self.dependency_types:
                    name = self._get_full_name(node)
                    dep_elements = name_to_element.get(name, set())
                    for dep_element in dep_elements:
                        dependency = Dependency(
                            code_element=self.source,
                            depends_on_code_element=dep_element,
                            dependency_type='attribute_access',
                            line=node.lineno,
                            column=node.col_offset
                        )
                        self.dependencies.add(dependency)
                self.generic_visit(node)

            def visit_Name(self, node):
                logging.debug(f"Visiting Name node: {node.id} at line {node.lineno}")
                if 'name_load' in self.dependency_types:
                    if isinstance(node.ctx, ast.Load):
                        name = node.id
                        dep_elements = name_to_element.get(name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.source,
                                depends_on_code_element=dep_element,
                                dependency_type='name_load',
                                line=node.lineno,
                                column=node.col_offset
                            )
                            self.dependencies.add(dependency)
                self.generic_visit(node)

        visitor = DependencyVisitor(dependencies, code_element, self.dependency_types)
        logging.debug(f"Starting AST traversal for {code_element.name}")
        visitor.visit(tree)
        logging.debug(f"Completed AST traversal for {code_element.name}")
        return dependencies
