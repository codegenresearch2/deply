from ..models.code_element import CodeElement
from ..models.violation import Violation


class BaseRule:
    def check(
            self,
            code_element_to_layer: dict[CodeElement, str],
            code_element_dependencies: dict[CodeElement, set[tuple[CodeElement, int]]],
    ) -> list[Violation]:
        raise NotImplementedError
