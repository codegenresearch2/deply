from abc import ABC, abstractmethod
from pathlib import Path
from typing import Set
from deply.models.code_element import CodeElement

class BaseCollector(ABC):
    @abstractmethod
    def collect(self) -> Set[CodeElement]:
        pass

class BoolCollector(BaseCollector):
    def collect(self) -> Set[CodeElement]:
        # Implementation for BoolCollector
        pass

class ClassInheritsCollector(BaseCollector):
    def collect(self) -> Set[CodeElement]:
        # Implementation for ClassInheritsCollector
        pass

class ClassNameRegexCollector(BaseCollector):
    def collect(self) -> Set[CodeElement]:
        # Implementation for ClassNameRegexCollector
        pass

class DecoratorUsageCollector(BaseCollector):
    def collect(self) -> Set[CodeElement]:
        # Implementation for DecoratorUsageCollector
        pass

class DirectoryCollector(BaseCollector):
    def collect(self) -> Set[CodeElement]:
        # Implementation for DirectoryCollector
        pass

class FileRegexCollector(BaseCollector):
    def collect(self) -> Set[CodeElement]:
        # Implementation for FileRegexCollector
        pass