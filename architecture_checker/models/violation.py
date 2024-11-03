from dataclasses import dataclass
from pathlib import Path


@dataclass
class Violation:
    file: Path
    class_name: str
    line: int
    message: str
