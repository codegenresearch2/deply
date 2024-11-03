from pathlib import Path
from typing import Set
from .base_collector import BaseCollector


class ExtCollector(BaseCollector):
    def __init__(self, config: dict, project_root: Path):
        self.extension = config.get("extension", "")
        if not self.extension.startswith("."):
            self.extension = f".{self.extension}"
        self.project_root = project_root

    def collect(self) -> Set[Path]:
        return set(self.project_root.rglob(f"*{self.extension}"))
