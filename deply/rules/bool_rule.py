from typing import Dict, Any, Optional
from deply.models.code_element import CodeElement
from deply.models.violation import Violation
from deply.models.violation_types import ViolationType
from deply.rules.base_rule import BaseRule


class BoolRule(BaseRule):
    VIOLATION_TYPE = ViolationType.BOOL_RULE

    def __init__(self, layer_name: str, config: Dict[str, Any]):
        self.layer_name = layer_name
        self.must_configs = config.get('must', [])
        self.any_of_configs = config.get('any_of', [])
        self.must_not_configs = config.get('must_not', [])

        from deply.rules.rule_factory import RuleFactory
        self.must_rules = RuleFactory.create_sub_rules(self.must_configs, layer_name)
        self.any_of_rules = RuleFactory.create_sub_rules(self.any_of_configs, layer_name)
        self.must_not_rules = RuleFactory.create_sub_rules(self.must_not_configs, layer_name)

    def check_element(self, layer_name: str, element: CodeElement) -> Optional[Violation]:
        if layer_name != self.layer_name:
            return None

        must_violation = self._check_must_rules(layer_name, element)
        if must_violation:
            return must_violation

        any_of_violation = self._check_any_of_rules(layer_name, element)
        if any_of_violation:
            return any_of_violation

        must_not_violation = self._check_must_not_rules(layer_name, element)
        if must_not_violation:
            return must_not_violation

        return None

    def _check_must_rules(self, layer_name: str, element: CodeElement) -> Optional[Violation]:
        for rule in self.must_rules:
            violation = rule.check_element(layer_name, element)
            if violation:
                return violation
        return None

    def _check_any_of_rules(self, layer_name: str, element: CodeElement) -> Optional[Violation]:
        if not self.any_of_rules:
            return None

        passed = False
        last_violation = None
        for rule in self.any_of_rules:
            violation = rule.check_element(layer_name, element)
            if violation is None:
                passed = True
                break
            last_violation = violation

        if not passed and last_violation:
            return last_violation

        return None

    def _check_must_not_rules(self, layer_name: str, element: CodeElement) -> Optional[Violation]:
        for rule in self.must_not_rules:
            violation = rule.check_element(layer_name, element)
            if violation is None:
                return Violation(
                    file=element.file,
                    element_name=element.name,
                    element_type=element.element_type,
                    line=element.line,
                    column=element.column,
                    message=(
                        f"BoolRule failed: must_not rule {rule.__class__.__name__} "
                        f"did not produce a violation."
                    ),
                    violation_type=self.VIOLATION_TYPE
                )
        return None
