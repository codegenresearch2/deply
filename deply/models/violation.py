from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Violation:
    file: Path
    element_name: str
    element_type: str  # 'class', 'function', or 'variable'
    line: int
    column: int
    message: str
