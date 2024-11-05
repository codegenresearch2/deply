from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodeElement:
    file: Path
    name: str  # Name of the code element (class, function, variable)
    element_type: str  # 'class', 'function', or 'variable'
