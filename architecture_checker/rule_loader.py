import importlib
import re


def camel_to_snake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def load_rules(config, project_root):
    rules = []
    rules_config = config.get('rules', [])
    for rule_cfg in rules_config:
        if rule_cfg.get('enabled', False):
            rule_name = rule_cfg['name']
            params = rule_cfg.get('params', {})
            module_name = f"architecture_checker.rules.{camel_to_snake(rule_name)}"
            class_name = rule_name
            try:
                module = importlib.import_module(module_name)
                rule_class = getattr(module, class_name)
                rule_instance = rule_class(project_root, params)
                rules.append(rule_instance)
            except (ModuleNotFoundError, AttributeError) as e:
                print(f"Error loading rule {rule_name}: {e}")
    return rules
