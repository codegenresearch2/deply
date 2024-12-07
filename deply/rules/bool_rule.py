from typing import Dict, Any, List, Optional
from deply.models.code_element import CodeElement
from deply.models.violation import Violation
from deply.rules.base_rule import BaseRule


class BoolRule(BaseRule):
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

        # must: all must pass (no violations)
        for r in self.must_rules:
            v = r.check_element(layer_name, element)
            if v:
                # This means this must rule failed by producing a violation
                return Violation(
                    file=element.file,
                    element_name=element.name,
                    element_type=element.element_type,
                    line=element.line,
                    column=element.column,
                    message=f"BoolRule failed: must rule {r.__class__.__name__} produced a violation."
                )

        # any_of: at least one must pass (no violation)
        if self.any_of_rules:
            any_passed = False
            for r in self.any_of_rules:
                v = r.check_element(layer_name, element)
                if not v:
                    # This rule passed (no violation)
                    any_passed = True
                    break
            if not any_passed:
                return Violation(
                    file=element.file,
                    element_name=element.name,
                    element_type=element.element_type,
                    line=element.line,
                    column=element.column,
                    message="BoolRule failed: none of the any_of rules passed."
                )

        # must_not: all must fail (all must produce violations)
        for r in self.must_not_rules:
            v = r.check_element(layer_name, element)
            if not v:
                # must_not rule did not produce violation, meaning it passed, which we don't want
                return Violation(
                    file=element.file,
                    element_name=element.name,
                    element_type=element.element_type,
                    line=element.line,
                    column=element.column,
                    message=f"BoolRule failed: must_not rule {r.__class__.__name__} did not produce a violation."
                )

        # If we reached here, all conditions are satisfied
        return None
