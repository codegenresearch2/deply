# rules/dependency_rule.py
from typing import Dict, List, Set

from deply.models.code_element import CodeElement
from deply.models.layer import Layer
from deply.models.violation import Violation
from deply.rules import BaseRule


class DependencyRule(BaseRule):
    def __init__(self, ruleset: Dict[str, Dict[str, List[str]]]):
        self.ruleset = ruleset

    def check(self, layers: Dict[str, Layer]) -> List[Violation]:
        violations: Set[Violation] = set()

        # Build a mapping from CodeElement to Layer name for quick lookup
        code_element_to_layer: Dict[CodeElement, str] = {}
        for layer_name, layer in layers.items():
            for code_element in layer.code_elements:
                code_element_to_layer[code_element] = layer_name

        # Iterate through each layer to check its dependencies
        for layer_name, layer in layers.items():
            layer_rules = self.ruleset.get(layer_name, {})
            allowed_layers = set(layer_rules.get("allow", []))
            disallowed_layers = set(layer_rules.get("disallow", []))

            for dependency in layer.dependencies:
                source_element = dependency.code_element
                target_element = dependency.depends_on_code_element

                # Determine the layer of the target element
                target_layer = code_element_to_layer.get(target_element)

                # Skip if the dependency is within the same layer or target layer is undefined
                if not target_layer or target_layer == layer_name:
                    continue

                # Check against disallowed layers
                if target_layer in disallowed_layers:
                    message = (
                        f"Layer '{layer_name}' is not allowed to depend on layer '{target_layer}'. "
                        f"Dependency type: {dependency.dependency_type}."
                    )
                    violation = Violation(
                        file=source_element.file,
                        element_name=source_element.name,
                        element_type=source_element.element_type,
                        line=dependency.line,
                        column=dependency.column,
                        message=message,
                    )
                    violations.add(violation)

                # Check against allowed layers if "allow" is specified
                if allowed_layers and target_layer not in allowed_layers:
                    message = (
                        f"Layer '{layer_name}' depends on unallowed layer '{target_layer}'. "
                        f"Dependency type: {dependency.dependency_type}."
                    )
                    violation = Violation(
                        file=source_element.file,
                        element_name=source_element.name,
                        element_type=source_element.element_type,
                        line=dependency.line,
                        column=dependency.column,
                        message=message,
                    )
                    violations.add(violation)

        return list(violations)
