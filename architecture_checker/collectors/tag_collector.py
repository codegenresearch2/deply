from pathlib import Path
from typing import Set
from .base_collector import BaseCollector
from ..utils.file_utils import get_python_files
import ast


class TagCollector(BaseCollector):
    def __init__(self, config: dict, project_root: Path):
        self.tag = config.get("tag", "")
        self.project_root = project_root

    def collect(self) -> Set[Path]:
        python_files = get_python_files(self.project_root)
        matched_files = set()
        for file_path in python_files:
            if self._file_contains_tag(file_path):
                matched_files.add(file_path)
        return matched_files

    def _file_contains_tag(self, file_path: Path) -> bool:
        with file_path.open('r', encoding='utf-8') as f:
            source = f.read()
        return self.tag in source
