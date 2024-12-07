from typing import Optional
from deply.rules.base_rule import BaseRule
from deply.models.code_element import CodeElement
from deply.models.violation import Violation


class InheritanceRule(BaseRule):
    def __init__(self, layer_name: str, base_class: str):
        self.layer_name = layer_name
        self.base_class = base_class

    def check_element(
            self,
            layer_name: str,
            element: CodeElement
    ) -> Optional[Violation]:
        if layer_name == self.layer_name and element.element_type == 'class':
            # Check if any inherited class matches exactly or ends with ".BaseClass"
            if not any(inh == self.base_class or inh.endswith(f".{self.base_class}") for inh in element.inherits):
                return Violation(
                    file=element.file,
                    element_name=element.name,
                    element_type=element.element_type,
                    line=element.line,
                    column=element.column,
                    message=f"Class '{element.name}' must inherit from '{self.base_class}'"
                )
        return None
