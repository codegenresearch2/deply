import re
from typing import Optional
from .base_rule import BaseRule
from ..models.violation import Violation
from ..models.code_element import CodeElement


class FunctionNamingRule(BaseRule):
    def __init__(self, layer_name: str, regex: str):
        self.layer_name = layer_name
        self.regex = re.compile(regex)

    def check_element(self, layer_name: str, element: CodeElement) -> Optional[Violation]:
        if layer_name == self.layer_name and element.element_type == 'function':
            func_name = element.name.split('.')[-1]
            if not self.regex.match(func_name):
                return Violation(
                    file=element.file,
                    element_name=element.name,
                    element_type=element.element_type,
                    line=element.line,
                    column=element.column,
                    message=f"Function '{element.name}' does not match naming pattern '{self.regex.pattern}'"
                )
        return None
