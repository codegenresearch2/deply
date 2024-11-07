from ..collectors.base_collector import BaseCollector
from ..models.code_element import CodeElement


class Layer:
    def __init__(self, name: str, collectors: list[BaseCollector]):
        self.name = name
        self.collectors = collectors

    def collect(self) -> set[CodeElement]:
        elements = set()
        for collector in self.collectors:
            elements.update(collector.collect())
        return elements
