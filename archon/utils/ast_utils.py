import ast
from pathlib import Path
from typing import Set, List, Dict, Tuple

from archon.models.code_element import CodeElement


def parse_file(file_path: Path) -> ast.AST:
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()
    return ast.parse(content, filename=str(file_path))


def get_classes_in_file(tree: ast.AST) -> Set[str]:
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def get_classes_inheriting(
        tree: ast.AST,
        base_class_name: str,
        file_path: Path,
        project_root: Path
) -> Set[CodeElement]:
    import_aliases = get_import_aliases(tree)
    classes = set()
    module_name = get_module_name(file_path, project_root)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = get_base_name(base, import_aliases)
                if base_name == base_class_name:
                    # Create the fully qualified class name
                    fq_class_name = f"{module_name}.{node.name}"
                    classes.add(CodeElement(file=file_path, class_name=fq_class_name))
    return classes


def get_module_name(file_path: Path, project_root: Path) -> str:
    relative_path = file_path.relative_to(project_root)
    if relative_path.stem == '__init__':
        relative_path = relative_path.parent
    else:
        relative_path = relative_path.with_suffix('')
    module_parts = relative_path.parts
    module_name = '.'.join(module_parts)
    return module_name


def get_full_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{get_full_name(node.value)}.{node.attr}"
    else:
        return ""


def get_imports(tree: ast.AST) -> List[Dict[str, any]]:
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({'module': alias.name, 'line': node.lineno})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                imports.append({'module': full_name, 'line': node.lineno})
    return imports


def get_class_dependencies(tree: ast.AST, import_aliases: Dict[str, str], file_path: Path) -> dict[
    CodeElement, set[tuple[str, int]]]:
    dependencies = {}
    class_defs = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    for class_def in class_defs:
        class_name = class_def.name
        class_code_element = CodeElement(file=file_path, class_name=class_name)
        class_dependencies = set()
        # Collect base classes
        for base in class_def.bases:
            base_name = get_base_name(base, import_aliases)
            if base_name:
                line_number = base.lineno if hasattr(base, 'lineno') else 0
                class_dependencies.add((base_name, line_number))
        # Collect used classes in method bodies
        for node in ast.walk(class_def):
            # Handle attribute access and names
            if isinstance(node, ast.Name):
                name = node.id
                resolved_name = import_aliases.get(name, name)
                line_number = node.lineno if hasattr(node, 'lineno') else 0
                class_dependencies.add((resolved_name, line_number))
            elif isinstance(node, ast.Attribute):
                full_name = get_full_name(node)
                parts = full_name.split('.')
                if parts[0] in import_aliases:
                    resolved_name = '.'.join([import_aliases[parts[0]]] + parts[1:])
                    line_number = node.lineno if hasattr(node, 'lineno') else 0
                    class_dependencies.add((resolved_name, line_number))
                else:
                    line_number = node.lineno if hasattr(node, 'lineno') else 0
                    class_dependencies.add((full_name, line_number))
        dependencies[class_code_element] = class_dependencies
    return dependencies


def get_class_names(tree: ast.AST) -> Set[str]:
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def get_import_aliases(tree: ast.AST) -> Dict[str, str]:
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                aliases[alias.asname or alias.name] = full_name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
    return aliases


def get_base_name(base: ast.expr, import_aliases: Dict[str, str]) -> str:
    if isinstance(base, ast.Name):
        return import_aliases.get(base.id, base.id)  # Resolve alias if any
    elif isinstance(base, ast.Attribute):
        full_name = get_full_name(base)
        parts = full_name.split('.')
        # Resolve the first part if it's an alias
        resolved_first = import_aliases.get(parts[0], parts[0])
        resolved_name = '.'.join([resolved_first] + parts[1:])
        return resolved_name
    return ""
