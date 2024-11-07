from typing import List
from ..models.violation import Violation
from .formats.text_report import TextReport


class ReportGenerator:
    def __init__(self, violations: List[Violation]):
        self.violations = violations

    def generate(self, format: str) -> str:
        if format == "text":
            return TextReport(self.violations).generate()
        else:
            raise ValueError(f"Unknown report format: {format}")
