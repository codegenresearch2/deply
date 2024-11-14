from dataclasses import dataclass

from deply.models.code_element import CodeElement


@dataclass(frozen=True)
class Dependency:
    code_element: CodeElement
    depends_on_code_element: CodeElement
    dependency_type: str
    line: int
    column: int
