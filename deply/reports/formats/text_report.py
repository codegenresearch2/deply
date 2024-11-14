from ...models.violation import Violation


class TextReport:
    def __init__(self, violations: list[Violation]):
        self.violations = violations

    def generate(self) -> str:
        lines = set()
        for violation in self.violations:
            lines.add(
                f"{violation.file}:{violation.line}:{violation.column} - {violation.message}"
                # + f" ({violation.element_type} '{violation.element_name}')"
            )
        return "\n".join(lines)
