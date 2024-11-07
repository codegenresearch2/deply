from .base_rule import BaseRule
from ..models.code_element import CodeElement
from ..models.violation import Violation


class DependencyRule(BaseRule):
    def __init__(self, ruleset: dict[str, dict[str, list[str]]]):
        self.ruleset = ruleset

    def check(
            self,
            code_element_to_layer: dict[CodeElement, str],
            code_element_dependencies: dict[CodeElement, set[tuple[CodeElement, int]]],
    ) -> list[Violation]:
        violations = []
        for code_element, layer_name in code_element_to_layer.items():
            layer_rules = self.ruleset.get(layer_name, {})
            allowed_layers = set(layer_rules.get("allow", []))
            disallowed_layers = set(layer_rules.get("disallow", []))
            dependencies = code_element_dependencies.get(code_element, set())
            for dep_element, line_number in dependencies:
                dep_layer = code_element_to_layer.get(dep_element)

                if dep_layer and dep_layer != layer_name:
                    if dep_layer in disallowed_layers:

                        message = f"Layer '{layer_name}' is not allowed to depend on layer '{dep_layer}'"
                        violations.append(
                            Violation(
                                file=code_element.file,
                                element_name=code_element.name,
                                element_type=code_element.element_type,
                                line=line_number,
                                message=message,
                            )
                        )
                    elif allowed_layers and dep_layer not in allowed_layers:
                        message = f"Layer '{layer_name}' depends on unallowed layer '{dep_layer}'"
                        violations.append(
                            Violation(
                                file=code_element.file,
                                element_name=code_element.name,
                                element_type=code_element.element_type,
                                line=line_number,
                                message=message,
                            )
                        )
        return violations
