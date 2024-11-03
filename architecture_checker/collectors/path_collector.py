from pathlib import Path
from typing import Set
from .base_collector import BaseCollector
from ..utils.file_utils import get_python_files_in_path


class PathCollector(BaseCollector):
    def __init__(self, config: dict, project_root: Path):
        self.path = project_root / config.get("path", "")
        self.project_root = project_root

    def collect(self) -> Set[Path]:
        return get_python_files_in_path(self.path)
