from pathlib import Path
from typing import Dict, Any, List, Set
from .models.layer import Layer
from .collectors.collector_factory import CollectorFactory
from .rules.rule_factory import RuleFactory
from .models.violation import Violation
from .models.code_element import CodeElement
from .utils.ast_utils import parse_file, get_import_aliases, get_class_dependencies


class CodeAnalyzer:
    def __init__(self, config: Dict[str, Any], project_root: Path):
        self.config = config
        self.project_root = project_root
        self.layers = self._initialize_layers()
        self.rules = self._initialize_rules()
        self.code_elements: Dict[CodeElement, str] = {}
        self.class_to_layer: Dict[str, str] = {}
        self.class_dependencies: Dict[CodeElement, Set[str]] = {}

    def _initialize_layers(self) -> Dict[str, Layer]:
        layers = {}
        for layer_config in self.config.get("layers", []):
            name = layer_config["name"]
            collectors_config = layer_config.get("collectors", [])
            collectors = [CollectorFactory.create(c, self.project_root) for c in collectors_config]
            layers[name] = Layer(name=name, collectors=collectors)
        return layers

    def _initialize_rules(self):
        ruleset = self.config.get("ruleset", {})
        rules = RuleFactory.create_rules(ruleset)
        return rules

    def analyze(self) -> List[Violation]:
        self._collect_code_elements()
        self._collect_class_dependencies()
        violations = []
        for rule in self.rules:
            violations.extend(rule.check(self.code_elements, self.class_dependencies, self.class_to_layer))
        return violations

    def _collect_code_elements(self):
        for layer in self.layers.values():
            elements = layer.collect()
            for element in elements:
                self.code_elements[element] = layer.name
                self.class_to_layer[element.class_name] = layer.name

                # print('-------------------------', flush=True)
                # print(element, flush=True)
                # print(element.class_name, flush=True)
                # print(layer.name, flush=True)
                # print('-------------------------', flush=True)


    def _collect_class_dependencies(self):
        for code_element in self.code_elements.keys():
            tree = parse_file(code_element.file)
            import_aliases = get_import_aliases(tree)
            class_deps = get_class_dependencies(tree, import_aliases, code_element.file)
            # Merge the dependencies for classes we have collected
            for class_elem, deps in class_deps.items():
                if class_elem in self.code_elements:
                    self.class_dependencies[class_elem] = deps
