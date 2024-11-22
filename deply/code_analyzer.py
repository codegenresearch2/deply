import ast
import logging
from typing import Dict, Set, List, Callable

from deply.models.code_element import CodeElement
from deply.models.dependency import Dependency


class CodeAnalyzer:
    def __init__(
            self,
            code_elements: Set[CodeElement],
            dependency_handler: Callable[[Dependency], None],
            dependency_types: List[str] = None
    ):
        self.code_elements = code_elements
        self.dependency_handler = dependency_handler
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
        logging.debug(f"Initialized CodeAnalyzer with {len(self.code_elements)} code elements.")

    def analyze(self) -> None:
        logging.debug("Starting analysis of code elements.")
        name_to_elements = self._build_name_to_element_map()
        logging.debug(f"Name to elements map built with {len(name_to_elements)} names.")

        file_to_elements: Dict[str, Set[CodeElement]] = {}
        for code_element in self.code_elements:
            file_to_elements.setdefault(code_element.file, set()).add(code_element)

        for file_path, elements_in_file in file_to_elements.items():
            logging.debug(f"Analyzing file: {file_path} with {len(elements_in_file)} code elements")
            self._extract_dependencies_from_file(file_path, elements_in_file, name_to_elements)
        logging.debug("Completed analysis of code elements.")

    def _build_name_to_element_map(self) -> Dict[str, Set[CodeElement]]:
        logging.debug("Building name to element map.")
        name_to_element = {}
        for elem in self.code_elements:
            name_to_element.setdefault(elem.name, set()).add(elem)
        logging.debug(f"Name to element map contains {len(name_to_element)} entries.")
        return name_to_element

    def _extract_dependencies_from_file(
            self,
            file_path: str,
            code_elements_in_file: Set[CodeElement],
            name_to_element: Dict[str, Set[CodeElement]]
    ) -> None:
        logging.debug(f"Extracting dependencies from file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            logging.debug(f"File {file_path} read successfully.")
            tree = ast.parse(source_code, filename=str(file_path))
            logging.debug(f"AST parsing completed for {file_path}.")
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError) as e:
            logging.warning(f"Failed to parse {file_path}: {e}")
            return

        elements_in_file_by_name = {elem.name: elem for elem in code_elements_in_file}

        class DependencyVisitor(ast.NodeVisitor):
            def __init__(
                    self,
                    code_elements_in_file: Dict[str, CodeElement],
                    dependency_types: List[str],
                    dependency_handler: Callable[[Dependency], None]
            ):
                self.code_elements_in_file = code_elements_in_file
                self.dependency_types = dependency_types
                self.dependency_handler = dependency_handler
                self.current_code_element = None
                logging.debug(f"DependencyVisitor created for file with {len(code_elements_in_file)} code elements")

            def visit_FunctionDef(self, node):
                self.current_code_element = self.code_elements_in_file.get(node.name)
                if 'decorator' in self.dependency_types and self.current_code_element:
                    self._process_decorators(node)
                if 'type_annotation' in self.dependency_types and self.current_code_element:
                    if node.returns:
                        self._process_annotation(node.returns)
                    for arg in node.args.args + node.args.kwonlyargs:
                        if arg.annotation:
                            self._process_annotation(arg.annotation)
                self.generic_visit(node)
                self.current_code_element = None

            def visit_ClassDef(self, node):
                self.current_code_element = self.code_elements_in_file.get(node.name)
                if 'class_inheritance' in self.dependency_types and self.current_code_element:
                    for base in node.bases:
                        base_name = self._get_full_name(base)
                        dep_elements = name_to_element.get(base_name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.current_code_element,
                                depends_on_code_element=dep_element,
                                dependency_type='class_inheritance',
                                line=base.lineno,
                                column=base.col_offset
                            )
                            self.dependency_handler(dependency)
                if 'decorator' in self.dependency_types and self.current_code_element:
                    self._process_decorators(node)
                if 'metaclass' in self.dependency_types and self.current_code_element:
                    for keyword in node.keywords:
                        if keyword.arg == 'metaclass':
                            metaclass_name = self._get_full_name(keyword.value)
                            dep_elements = name_to_element.get(metaclass_name, set())
                            for dep_element in dep_elements:
                                dependency = Dependency(
                                    code_element=self.current_code_element,
                                    depends_on_code_element=dep_element,
                                    dependency_type='metaclass',
                                    line=keyword.value.lineno,
                                    column=keyword.value.col_offset
                                )
                                self.dependency_handler(dependency)
                self.generic_visit(node)
                self.current_code_element = None

            def _process_decorators(self, node):
                for decorator in node.decorator_list:
                    decorator_name = self._get_full_name(decorator)
                    dep_elements = name_to_element.get(decorator_name, set())
                    for dep_element in dep_elements:
                        dependency = Dependency(
                            code_element=self.current_code_element,
                            depends_on_code_element=dep_element,
                            dependency_type='decorator',
                            line=decorator.lineno,
                            column=decorator.col_offset
                        )
                        self.dependency_handler(dependency)

            def _process_annotation(self, annotation):
                annotation_name = self._get_full_name(annotation)
                dep_elements = name_to_element.get(annotation_name, set())
                for dep_element in dep_elements:
                    dependency = Dependency(
                        code_element=self.current_code_element,
                        depends_on_code_element=dep_element,
                        dependency_type='type_annotation',
                        line=getattr(annotation, 'lineno', 0),
                        column=getattr(annotation, 'col_offset', 0)
                    )
                    self.dependency_handler(dependency)

            def visit_Call(self, node):
                if 'function_call' in self.dependency_types and self.current_code_element:
                    if isinstance(node.func, ast.Name):
                        name = node.func.id
                        dep_elements = name_to_element.get(name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.current_code_element,
                                depends_on_code_element=dep_element,
                                dependency_type='function_call',
                                line=node.lineno,
                                column=node.col_offset
                            )
                            self.dependency_handler(dependency)
                    elif isinstance(node.func, ast.Attribute):
                        full_name = self._get_full_name(node.func)
                        dep_elements = name_to_element.get(full_name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.current_code_element,
                                depends_on_code_element=dep_element,
                                dependency_type='function_call',
                                line=node.lineno,
                                column=node.col_offset
                            )
                            self.dependency_handler(dependency)
                self.generic_visit(node)

            def visit_Import(self, node):
                if 'import' in self.dependency_types:
                    for alias in node.names:
                        name = alias.asname or alias.name.split('.')[0]
                        dep_elements = name_to_element.get(name, set())
                        for dep_element in dep_elements:
                            for code_element in self.code_elements_in_file.values():
                                dependency = Dependency(
                                    code_element=code_element,
                                    depends_on_code_element=dep_element,
                                    dependency_type='import',
                                    line=node.lineno,
                                    column=node.col_offset
                                )
                                self.dependency_handler(dependency)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if 'import_from' in self.dependency_types:
                    for alias in node.names:
                        name = alias.asname or alias.name
                        dep_elements = name_to_element.get(name, set())
                        for dep_element in dep_elements:
                            for code_element in self.code_elements_in_file.values():
                                dependency = Dependency(
                                    code_element=code_element,
                                    depends_on_code_element=dep_element,
                                    dependency_type='import_from',
                                    line=node.lineno,
                                    column=node.col_offset
                                )
                                self.dependency_handler(dependency)
                self.generic_visit(node)

            def visit_Name(self, node):
                if 'name_load' in self.dependency_types and self.current_code_element:
                    if isinstance(node.ctx, ast.Load):
                        name = node.id
                        dep_elements = name_to_element.get(name, set())
                        for dep_element in dep_elements:
                            dependency = Dependency(
                                code_element=self.current_code_element,
                                depends_on_code_element=dep_element,
                                dependency_type='name_load',
                                line=node.lineno,
                                column=node.col_offset
                            )
                            self.dependency_handler(dependency)
                self.generic_visit(node)

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

        visitor = DependencyVisitor(
            code_elements_in_file=elements_in_file_by_name,
            dependency_types=self.dependency_types,
            dependency_handler=self.dependency_handler
        )
        logging.debug(f"Starting AST traversal for file: {file_path}")
        visitor.visit(tree)
        logging.debug(f"Completed AST traversal for file: {file_path}")
