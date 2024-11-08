from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodeElement:
    file: Path
    name: str
    element_type: str  # 'class', 'function', or 'variable'
    line: int
    column: int
