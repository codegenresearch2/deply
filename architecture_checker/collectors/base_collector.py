from abc import ABC, abstractmethod
from ..models.code_element import CodeElement


class BaseCollector(ABC):
    @abstractmethod
    def collect(self) -> set[CodeElement]:
        pass
