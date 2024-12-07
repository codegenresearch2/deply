# deply/models/code_element.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, FrozenSet


@dataclass(frozen=True)
class CodeElement:
    file: Path
    name: str  # Should include fully qualified name if possible
    element_type: str  # 'class', 'function', or 'variable'
    line: int
    column: int

    decorators: Tuple[str, ...] = field(default_factory=tuple)
    inherits: Tuple[str, ...] = field(default_factory=tuple)
    return_annotation: Optional[str] = None
    type_annotations: FrozenSet[Tuple[str, str]] = field(default_factory=frozenset)
