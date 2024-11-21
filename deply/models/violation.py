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

    def __hash__(self):
        return hash((self.file, self.line, self.column, self.message))

    def __eq__(self, other):
        return (
                (self.file, self.line, self.column, self.message)
                == (other.file, other.line, other.column, other.message)
        )
