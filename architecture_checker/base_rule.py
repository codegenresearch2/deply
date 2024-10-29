from abc import ABC, abstractmethod


class BaseRule(ABC):
    def __init__(self, project_root, params):
        self.project_root = project_root
        self.params = params
        self.violations = []

    @abstractmethod
    def run(self):
        pass

    def report(self):
        return self.violations
