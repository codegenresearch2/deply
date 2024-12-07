from typing import List, Optional

from deply.models.dependency import Dependency
from deply.models.violation import Violation
from deply.rules.base_rule import BaseRule


class DependencyRule(BaseRule):
    def __init__(self, layer_name: str, disallowed_layers: List[str]):
        self.layer_name = layer_name
        self.disallowed_layers = set(disallowed_layers)

    def check(
            self,
            source_layer: str,
            target_layer: str,
            dependency: Dependency
    ) -> Optional[Violation]:
        if source_layer == self.layer_name and target_layer in self.disallowed_layers:
            message = (
                f"Layer '{source_layer}' is not allowed to depend on layer '{target_layer}'. "
                f"Dependency type: {dependency.dependency_type}."
            )
            return Violation(
                file=dependency.code_element.file,
                element_name=dependency.code_element.name,
                element_type=dependency.code_element.element_type,
                line=dependency.line,
                column=dependency.column,
                message=message,
            )

        # No violation
        return None
