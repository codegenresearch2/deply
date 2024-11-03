from typing import Dict, Any, List
from .base_rule import BaseRule
from .dependency_rule import DependencyRule


class RuleFactory:
    @staticmethod
    def create_rules(ruleset: Dict[str, Any]) -> List[BaseRule]:
        return [DependencyRule(ruleset)]
