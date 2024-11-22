from ..models.dependency import Dependency
from ..models.violation import Violation


class BaseRule:
    def check(
            self,
            source_layer: str,
            target_layer: str,
            dependency: Dependency
    ) -> Violation:
        raise NotImplementedError
