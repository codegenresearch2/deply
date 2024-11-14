from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodeElement:
    file: Path
    name: str  # Should include fully qualified name if possible
    element_type: str  # 'class', 'function', or 'variable'
    line: int
    column: int
