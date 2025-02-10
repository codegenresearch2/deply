import ast
from pathlib import Path
from typing import Set
from ..models.code_element import CodeElement


class BaseCollector(ABC):
    def __init__(self, config: dict, paths: list[str], exclude_files: list[str]):
        self.config = config
        self.paths = paths
        self.exclude_files = exclude_files
        self.exclude_regex = re.compile(self.config.get("exclude_files_regex", "")) if self.config.get("exclude_files_regex", "") else None

    def collect(self) -> Set[CodeElement]:
        elements = set()
        for path in self.paths:
            if self.exclude_regex and self.exclude_regex.search(str(path)):
                continue
            elements.update(self.match_in_file(path))
        return elements

    def match_in_file(self, file_path: str) -> Set[CodeElement]:
        file_path = Path(file_path)
        with file_path.open('r') as file:
            file_content = file.read()
            file_ast = ast.parse(file_content, filename=str(file_path))
        
        return self._match_classes(file_ast, file_path)

    def _match_classes(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        import_aliases = get_import_aliases(file_ast)
        classes = set()
        for node in ast.walk(file_ast):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = get_base_name(base, import_aliases)
                    if base_name == self.base_class or base_name.endswith(f".{self.base_class}"):
                        full_name = self._get_full_name(node)
                        code_element = CodeElement(file=file_path, name=full_name, element_type="class", line=node.lineno, column=node.col_offset)
                        classes.add(code_element)
        return classes

    def _get_full_name(self, node):
        names = []
        current = node
        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):
            names.append(current.name)
            current = getattr(current, "parent", None)
        return ".".join(reversed(names))

    def annotate_parent(self, tree):
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node