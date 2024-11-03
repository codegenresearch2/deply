from pathlib import Path
from typing import Set


def get_python_files(root: Path) -> Set[Path]:
    return set(root.rglob("*.py"))


def get_python_files_in_path(path: Path) -> Set[Path]:
    if path.is_dir():
        return set(path.rglob("*.py"))
    elif path.is_file() and path.suffix == ".py":
        return {path}
    else:
        return set()


def get_all_files(root: Path) -> Set[Path]:
    return set(root.rglob('*'))
