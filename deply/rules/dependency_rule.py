from typing import Dict, List, Optional

from deply.models.dependency import Dependency
from deply.models.violation import Violation
from deply.rules import BaseRule


class DependencyRule(BaseRule):
    def __init__(self, ruleset: Dict[str, Dict[str, List[str]]]):
        self.ruleset = ruleset

    def check(
            self,
            source_layer: str,
            target_layer: str,
            dependency: Dependency
    ) -> Optional[Violation]:
        # Get the rules for the source layer
        layer_rules = self.ruleset.get(source_layer, {})
        allowed_layers = set(layer_rules.get("allow", []))
        disallowed_layers = set(layer_rules.get("disallow", []))

        # Check against disallowed layers
        if target_layer in disallowed_layers:
            message = (
                f"Layer '{source_layer}' is not allowed to depend on layer '{target_layer}'. "
                f"Dependency type: {dependency.dependency_type}."
            )
            violation = Violation(
                file=dependency.code_element.file,
                element_name=dependency.code_element.name,
                element_type=dependency.code_element.element_type,
                line=dependency.line,
                column=dependency.column,
                message=message,
            )
            return violation

        # Check against allowed layers if "allow" is specified
        if allowed_layers and target_layer not in allowed_layers:
            message = (
                f"Layer '{source_layer}' depends on unallowed layer '{target_layer}'. "
                f"Dependency type: {dependency.dependency_type}."
            )
            violation = Violation(
                file=dependency.code_element.file,
                element_name=dependency.code_element.name,
                element_type=dependency.code_element.element_type,
                line=dependency.line,
                column=dependency.column,
                message=message,
            )
            return violation

        # No violation
        return None
