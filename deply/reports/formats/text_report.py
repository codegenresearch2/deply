from ...models.violation import Violation


class TextReport:
    def __init__(self, violations: list[Violation]):
        self.violations = violations

    def generate(self) -> str:
        lines = []
        for violation in self.violations:
            lines.append(
                f"{violation.file}:{violation.line} - {violation.message} ({violation.element_type} {violation.element_name}) "
            )
        return "\n".join(lines)
