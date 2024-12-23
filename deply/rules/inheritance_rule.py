from typing import Optional

from deply.models.violation_types import ViolationType
from deply.rules.base_rule import BaseRule
from deply.models.code_element import CodeElement
from deply.models.violation import Violation


class InheritanceRule(BaseRule):
    VIOLATION_TYPE = ViolationType.INHERITANCE

    def __init__(self, layer_name: str, base_class: str):
        self.layer_name = layer_name
        self.base_class = base_class

    def check_element(self, layer_name: str, element: CodeElement) -> Optional[Violation]:
        if layer_name != self.layer_name or element.element_type != 'class':
            return None
        if any(
                inherited_class == self.base_class or inherited_class.endswith(f".{self.base_class}")
                for inherited_class in element.inherits
        ):
            return None
        return Violation(
            file=element.file,
            element_name=element.name,
            element_type=element.element_type,
            line=element.line,
            column=element.column,
            message=(
                f"Class '{element.name}' must inherit from '{self.base_class}'."
            ),
            violation_type=self.VIOLATION_TYPE
        )
