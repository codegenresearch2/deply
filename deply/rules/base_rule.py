from ..models.layer import Layer
from ..models.violation import Violation


class BaseRule:
    def check(self, layers: dict[str, Layer]) -> list[Violation]:
        raise NotImplementedError
