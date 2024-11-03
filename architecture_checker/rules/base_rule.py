from typing import List, Dict

from ..models.code_element import CodeElement
from ..models.violation import Violation


class BaseRule:
    def check(
            self,
            code_elements: Dict[CodeElement, str],
            class_dependencies: Dict[CodeElement, set[str]],
            class_to_layer: Dict[str, str]
    ) -> List[Violation]:
        raise NotImplementedError
