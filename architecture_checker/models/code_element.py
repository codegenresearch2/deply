from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodeElement:
    file: Path
    class_name: str
