from dataclasses import dataclass

from .dependency import Dependency
from ..models.code_element import CodeElement


@dataclass()
class Layer:
    name: str
    code_elements: set[CodeElement]
    dependencies: set[Dependency]
