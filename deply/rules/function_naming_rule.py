import re
from typing import Optional
from .base_rule import BaseRule
from ..models.violation import Violation
from ..models.code_element import CodeElement
from ..models.violation_types import ViolationType


class FunctionNamingRule(BaseRule):
    VIOLATION_TYPE = ViolationType.FUNCTION_NAMING

    def __init__(self, layer_name: str, regex: str):
        self.layer_name = layer_name
        self.function_name_pattern = re.compile(regex)

    def check_element(self, layer_name: str, element: CodeElement) -> Optional[Violation]:
        if layer_name != self.layer_name or element.element_type != 'function':
            return None
        function_name = element.name.split('.')[-1]
        if self.function_name_pattern.match(function_name):
            return None
        return Violation(
            file=element.file,
            element_name=element.name,
            element_type=element.element_type,
            line=element.line,
            column=element.column,
            message=(
                f"Function '{element.name}' does not match naming pattern '{self.function_name_pattern.pattern}'."
            ),
            violation_type=self.VIOLATION_TYPE
        )
