import ast\nimport re\nfrom pathlib import Path\nfrom typing import List, Set, Tuple\n\nfrom deply.collectors import BaseCollector\nfrom deply.models.code_element import CodeElement\n\nclass DirectoryCollector(BaseCollector):\n    def __init__(self, config: dict, paths: List[str], exclude_files: List[str]):\n        self.directories = config.get("directories", [])\n        self.recursive = config.get("recursive", True)\n        self.exclude_files_regex_pattern = config.get("exclude_files_regex", "")\n        self.element_type = config.get("element_type", "")\n        self.exclude_regex = re.compile(self.exclude_files_regex_pattern) if self.exclude_files_regex_pattern else None\n        self.base_paths = [Path(p) for p in paths]\n        self.exclude_files = [re.compile(pattern) for pattern in exclude_files]\n\n    def match_in_file(self, file_path: Path, file_ast: ast.AST) -> Set[CodeElement]:\n        elements = set()\n        if not self.element_type or self.element_type == 'class':\n            elements.update(self.get_class_names(file_ast, file_path))\n        if not self.element_type or self.element_type == 'function':\n            elements.update(self.get_function_names(file_ast, file_path))\n        if not self.element_type or self.element_type == 'variable':\n            elements.update(self.get_variable_names(file_ast, file_path))\n        return elements\n\n    def get_class_names(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:\n        classes = set()\n        for node in ast.walk(file_ast):\n            if isinstance(node, ast.ClassDef):\n                full_name = self._get_full_name(node)\n                code_element = CodeElement(file=file_path, name=full_name, element_type='class', line=node.lineno, column=node.col_offset)\n                classes.add(code_element)\n        return classes\n\n    def get_function_names(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:\n        functions = set()\n        for node in ast.walk(file_ast):\n            if isinstance(node, ast.FunctionDef):\n                full_name = self._get_full_name(node)\n                code_element = CodeElement(file=file_path, name=full_name, element_type='function', line=node.lineno, column=node.col_offset)\n                functions.add(code_element)\n        return functions\n\n    def get_variable_names(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:\n        variables = set()\n        for node in ast.walk(file_ast):\n            if isinstance(node, ast.Assign):\n                for target in node.targets:\n                    if isinstance(target, ast.Name):\n                        code_element = CodeElement(file=file_path, name=target.id, element_type='variable', line=target.lineno, column=target.col_offset)\n                        variables.add(code_element)\n        return variables\n\n    def _get_full_name(self, node):\n        names = []\n        current = node\n        while isinstance(current, (ast.ClassDef, ast.FunctionDef)):\n            names.append(current.name)\n            current = getattr(current, 'parent', None)\n        return '.'.join(reversed(names))\n\n    def get_all_files(self) -> List[Tuple[Path, Path]]:\n        all_files = []\n        for base_path in self.base_paths:\n            if not base_path.exists():\n                continue\n            for directory in self.directories:\n                dir_path = base_path / directory\n                if dir_path.exists() and dir_path.is_dir():\n                    if self.recursive:\n                        files = [f for f in dir_path.rglob('*.py') if f.is_file()]\n                    else:\n                        files = [f for f in dir_path.glob('*.py') if f.is_file()]\n                    files = [f for f in files if not self.should_exclude_file(f)]\n                    files_with_base = [(f, base_path) for f in files]\n                    all_files.extend(files_with_base)\n        return all_files\n\n    def should_exclude_file(self, file_path: Path) -> bool:\n        relative_path = str(file_path.relative_to(self.base_paths[0]))\n        return any(pattern.search(relative_path) for pattern in self.exclude_files) or (self.exclude_regex and self.exclude_regex.match(relative_path))\n\n    def parse_file(self, file_path: Path) -> ast.AST:\n        try:\n            with open(file_path, 'r', encoding='utf-8') as f:\n                return ast.parse(f.read(), filename=str(file_path))\n        except (SyntaxError, UnicodeDecodeError):\n            return None\n