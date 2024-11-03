from architecture_checker.models.code_element import CodeElement


class BaseCollector:
    def collect(self) -> set[CodeElement]:
        raise NotImplementedError
