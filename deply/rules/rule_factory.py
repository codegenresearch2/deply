from typing import Dict, Any, List
from .base_rule import BaseRule
from .dependency_rule import DependencyRule
from .class_naming_rule import ClassNamingRule
from .function_naming_rule import FunctionNamingRule
from .class_decorator_rule import ClassDecoratorUsageRule
from .function_decorator_rule import FunctionDecoratorUsageRule
from .inheritance_rule import InheritanceRule
from .bool_rule import BoolRule


class RuleFactory:
    @staticmethod
    def create_sub_rules(rule_configs: List[Dict[str, Any]], layer_name: str) -> List[BaseRule]:
        sub_rules: List[BaseRule] = []
        for rc in rule_configs:
            r_type = rc.get("type")
            if r_type == "class_name_regex":
                regex = rc.get("class_name_regex", "")
                sub_rules.append(ClassNamingRule(layer_name, regex))
            elif r_type == "function_name_regex":
                regex = rc.get("function_name_regex", "")
                sub_rules.append(FunctionNamingRule(layer_name, regex))
            elif r_type == "function_decorator_name_regex":
                regex = rc.get("decorator_name_regex", "")
                sub_rules.append(FunctionDecoratorUsageRule(layer_name, regex))
            elif r_type == "class_decorator_name_regex":
                regex = rc.get("decorator_name_regex", "")
                sub_rules.append(ClassDecoratorUsageRule(layer_name, regex))
            elif r_type == "class_inherits":
                base_class = rc.get("base_class", "")
                sub_rules.append(InheritanceRule(layer_name, base_class))
            elif r_type == "bool":
                sub_rules.append(BoolRule(layer_name, rc))
            # Add other rule types as needed
        return sub_rules

    @staticmethod
    def create_rules(ruleset: Dict[str, Any]) -> List[BaseRule]:
        all_rules: List[BaseRule] = []

        for layer_name, layer_rules in ruleset.items():
            # Disallow layer dependencies
            if "disallow_layer_dependencies" in layer_rules:
                disallowed = layer_rules["disallow_layer_dependencies"]
                all_rules.append(DependencyRule(layer_name, disallowed))

            # Enforce class naming
            if "enforce_class_naming" in layer_rules:
                for rule_config in layer_rules["enforce_class_naming"]:
                    if rule_config.get("type") == "class_name_regex":
                        regex = rule_config.get("class_name_regex", "")
                        all_rules.append(ClassNamingRule(layer_name, regex))
                    elif rule_config.get("type") == "bool":
                        all_rules.append(BoolRule(layer_name, rule_config))

            # Enforce function naming
            if "enforce_function_naming" in layer_rules:
                for rule_config in layer_rules["enforce_function_naming"]:
                    if rule_config.get("type") == "function_name_regex":
                        regex = rule_config.get("function_name_regex", "")
                        all_rules.append(FunctionNamingRule(layer_name, regex))
                    elif rule_config.get("type") == "bool":
                        all_rules.append(BoolRule(layer_name, rule_config))

            # Enforce class decorator usage
            if "enforce_class_decorator_usage" in layer_rules:
                for rule_config in layer_rules["enforce_class_decorator_usage"]:
                    if rule_config.get("type") == "class_decorator_name_regex":
                        regex = rule_config.get("decorator_name_regex", "")
                        all_rules.append(ClassDecoratorUsageRule(layer_name, regex))
                    elif rule_config.get("type") == "bool":
                        all_rules.append(BoolRule(layer_name, rule_config))

            # Enforce function decorator usage
            if "enforce_function_decorator_usage" in layer_rules:
                for rule_config in layer_rules["enforce_function_decorator_usage"]:
                    if rule_config.get("type") == "function_decorator_name_regex":
                        regex = rule_config.get("decorator_name_regex", "")
                        all_rules.append(FunctionDecoratorUsageRule(layer_name, regex))
                    elif rule_config.get("type") == "bool":
                        all_rules.append(BoolRule(layer_name, rule_config))

            # Enforce inheritance
            if "enforce_inheritance" in layer_rules:
                for rule_config in layer_rules["enforce_inheritance"]:
                    if rule_config.get("type") == "class_inherits":
                        base_class = rule_config.get("base_class", "")
                        all_rules.append(InheritanceRule(layer_name, base_class))
                    elif rule_config.get("type") == "bool":
                        all_rules.append(BoolRule(layer_name, rule_config))

        return all_rules
