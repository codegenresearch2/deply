from pathlib import Path
from typing import Set
from .base_collector import BaseCollector
from ..utils.file_utils import get_python_files


class FilenameCollector(BaseCollector):
    def __init__(self, config: dict, project_root: Path):
        self.filename = config.get("name", "")
        self.project_root = project_root

    def collect(self) -> Set[Path]:
        files = get_python_files(self.project_root)
        matched_files = {f for f in files if f.name == self.filename}
        return matched_files
