from .base_rule import BaseRule
from ..models.code_element import CodeElement
from ..models.violation import Violation


class DependencyRule(BaseRule):
    def __init__(self, ruleset: dict[str, dict[str, list[str]]]):
        self.ruleset = ruleset

    def check(
            self,
            code_elements: dict[CodeElement, str],
            class_dependencies: dict[CodeElement, set[str]],
            class_to_layer: dict[str, str],
    ) -> list[Violation]:
        violations = []
        for code_element, layer_name in code_elements.items():
            layer_rules = self.ruleset.get(layer_name, {})
            allowed_layers = set(layer_rules.get("allow", []))
            disallowed_layers = set(layer_rules.get("disallow", []))
            dependencies = class_dependencies.get(code_element, set())
            for dependency, line_number in dependencies:
                dependent_layer = class_to_layer.get(dependency)
                if dependent_layer and dependent_layer != layer_name:
                    if dependent_layer in disallowed_layers:
                        message = f"Layer '{layer_name}' is not allowed to depend on layer '{dependent_layer}'"
                        violations.append(
                            Violation(
                                file=code_element.file,
                                class_name=code_element.class_name,
                                line=line_number,
                                message=message,
                            )
                        )
                    elif allowed_layers and dependent_layer not in allowed_layers:
                        message = f"Layer '{layer_name}' depends on unallowed layer '{dependent_layer}'"
                        violations.append(
                            Violation(
                                file=code_element.file,
                                class_name=code_element.class_name,
                                line=line_number,
                                message=message,
                            )
                        )
        return violations
