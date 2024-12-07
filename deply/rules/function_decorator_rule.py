import re
from typing import Optional
from .base_rule import BaseRule
from ..models.violation import Violation
from ..models.code_element import CodeElement


class FunctionDecoratorUsageRule(BaseRule):
    def __init__(self, layer_name: str, decorator_regex: str):
        self.layer_name = layer_name
        self.regex = re.compile(decorator_regex)

    def check_element(self, layer_name: str, element: CodeElement) -> Optional[Violation]:
        # Assuming we have decorators info similar to ClassDecoratorUsageRule
        if layer_name == self.layer_name and element.element_type == 'function':
            decorators = getattr(element, 'decorators', [])
            if not any(self.regex.match(d) for d in decorators):
                return Violation(
                    file=element.file,
                    element_name=element.name,
                    element_type=element.element_type,
                    line=element.line,
                    column=element.column,
                    message=f"Function '{element.name}' must have a decorator matching '{self.regex.pattern}'"
                )
        return None
