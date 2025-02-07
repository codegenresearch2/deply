import ast\"import re\"from pathlib import Path\"from typing import List, Set, Tuple\"from deply.collectors import BaseCollector\"from deply.models.code_element import CodeElement\n\nclass DecoratorUsageCollector(BaseCollector):\n    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):\n        self.decorator_name = config.get('decorator_name', '')\n        self.decorator_regex_pattern = config.get('decorator_regex', '')\n        self.exclude_files_regex_pattern = config.get('exclude_files_regex', '')\n        self.decorator_regex = re.compile(self.decorator_regex_pattern) if self.decorator_regex_pattern else None\n        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None\n        self.paths = [Path(p) for p in paths]\n        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]\n\n    def collect(self) -> Set[CodeElement]:\n        collected_elements = set()\n        all_files = self.get_all_files()\n\n        for file_path, base_path in all_files:\n            tree = self.parse_file(file_path)\n            if tree is None:\n                continue\n            elements = self.match_in_file(file_ast=tree, file_path=file_path)\n            collected_elements.update(elements)\n\n        return collected_elements\n\n    def get_all_files(self) -> List[Tuple[Path, Path]]:\n        all_files = []\n\n        for base_path in self.paths:\n            if not base_path.exists():\n                continue\n\n            files = [f for f in base_path.rglob('*.py') if f.is_file()]\n\n            def is_excluded(file_path: Path) -> bool:\n                relative_path = str(file_path.relative_to(base_path))\n                return any(pattern.search(relative_path) for pattern in self.exclude_files)\n\n            files = [f for f in files if not is_excluded(f)]\n\n            if self.exclude_regex:\n                files = [f for f in files if not self.exclude_regex.match(str(f.relative_to(base_path)))]\n\n            files_with_base = [(f, base_path) for f in files]\n            all_files.extend(files_with_base)\n\n        return all_files\n\n    def parse_file(self, file_path: Path):\n        try:\n            with open(file_path, 'r', encoding='utf-8') as f:\n                return ast.parse(f.read(), filename=str(file_path))\n        except (SyntaxError, UnicodeDecodeError):\n            return None\n\n    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:\n        if self.exclude_regex and self.exclude_regex.search(str(file_path)):\n            return set()\n\n        elements = set()\n        for node in ast.walk(file_ast):\n            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):\n                for decorator in node.decorator_list:\n                    d_name = self._get_decorator_name(decorator)\n                    if self.decorator_name and d_name == self.decorator_name or \n                       self.decorator_regex and self.decorator_regex.match(d_name):\n                        full_name = self._get_full_name(node)\n                        code_element = CodeElement(\n                            file=file_path,\n                            name=full_name,\n                            element_type='function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class',\n                            line=node.lineno,\n                            column=node.col_offset\n                        )\n                        elements.add(code_element)\n        return elements\n\n    def _get_decorator_name(self, node):\n        if isinstance(node, ast.Name):\n            return node.id\n        elif isinstance(node, ast.Attribute):\n            return node.attr\n        elif isinstance(node, ast.Call):\n            return self._get_decorator_name(node.func)\n        else:\n            return ''\n\n    def _get_full_name(self, node):\n        if isinstance(node, ast.Name):\n            return node.id\n        elif isinstance(node, ast.Attribute):\n            value = self._get_full_name(node.value)\n            if value:\n                return f"{value}.{node.attr}"\n            else:\n                return node.attr\n        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):\n            names = []\n            current = node\n            while isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):\n                names.append(current.name)\n                current = getattr(current, 'parent', None)\n            return '.'.join(reversed(names))\n        elif isinstance(node, ast.Call):\n            return self._get_full_name(node.func)\n        else:\n            return ''\n\n    #def annotate_parent(self, tree):\n    #    for node in ast.walk(tree):\n    #        for child in ast.iter_child_nodes(node):\n    #            child.parent = node