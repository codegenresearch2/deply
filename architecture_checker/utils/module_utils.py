from pathlib import Path
from typing import Dict


def get_modules_in_project(project_root: Path) -> Dict[str, Path]:
    modules = {}
    for file_path in project_root.rglob("*.py"):
        if file_path.name == "__init__.py":
            continue
        relative_path = file_path.relative_to(project_root)
        module_name = ".".join(relative_path.with_suffix("").parts)
        modules[module_name] = file_path
    return modules
