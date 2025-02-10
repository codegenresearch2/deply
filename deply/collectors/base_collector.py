from abc import ABC, abstractmethod
from typing import Set
from ..models.code_element import CodeElement


class BaseCollector(ABC):
    @abstractmethod
    def collect(self) -> Set[CodeElement]:
        pass