import ast


def get_import_aliases(tree):
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                asname = alias.asname or alias.name
                aliases[asname] = name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                asname = alias.asname or alias.name
                aliases[asname] = full_name
    return aliases


def get_base_name(node, import_aliases):
    if isinstance(node, ast.Name):
        return import_aliases.get(node.id, node.id)
    elif isinstance(node, ast.Attribute):
        value = get_base_name(node.value, import_aliases)
        return f"{value}.{node.attr}"
    else:
        return ''
