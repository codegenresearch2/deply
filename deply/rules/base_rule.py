from typing import Optional
from ..models.dependency import Dependency
from ..models.violation import Violation
from ..models.code_element import CodeElement


class BaseRule:
    def check(
            self,
            source_layer: str,
            target_layer: str,
            dependency: Dependency
    ) -> Optional[Violation]:
        return None

    # New method for element-based checks
    def check_element(
            self,
            layer_name: str,
            element: CodeElement
    ) -> Optional[Violation]:
        return None
