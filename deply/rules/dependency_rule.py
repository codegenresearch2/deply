from .base_rule import BaseRule
from ..models.code_element import CodeElement
from ..models.layer import Layer
from ..models.violation import Violation


class DependencyRule(BaseRule):
    def __init__(self, ruleset: dict[str, dict[str, list[str]]]):
        self.ruleset = ruleset

    def check(self, layers: dict[str, Layer]) -> list[Violation]:
        violations = set()

        code_element_to_layer: dict[CodeElement, str] = {}
        for layer_name, layer in layers.items():
            for code_element in layer.code_elements:
                code_element_to_layer[code_element] = layer_name

        for layer_name, layer in layers.items():
            layer_rules = self.ruleset.get(layer_name, {})
            disallowed_layers = set(layer_rules.get("disallow", []))

            for dependency in layer.dependencies:
                source_element = dependency.code_element
                target_element = dependency.depends_on_code_element

                target_layer = code_element_to_layer.get(target_element)

                if not target_layer or target_layer == layer_name:
                    continue

                if target_layer in disallowed_layers:
                    message = (
                        f"Layer '{layer_name}' is not allowed to depend on layer '{target_layer}'. "
                    )
                    violation = Violation(
                        file=source_element.file,
                        element_name=source_element.name,
                        element_type=source_element.element_type,
                        line=dependency.line,
                        message=message,
                        column=dependency.column,
                    )
                    violations.add(violation)

        return list(violations)
