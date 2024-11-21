from ...models.violation import Violation


class TextReport:
    def __init__(self, violations: list[Violation]):
        self.violations = violations

    def generate(self) -> str:
        sorted_violations = sorted(
            self.violations,
            key=lambda v: (v.file, v.line, v.column)
        )
        lines = []
        for violation in sorted_violations:
            lines.append(
                f"{violation.file}:{violation.line}:{violation.column} - {violation.message}"
                # + f" ({violation.element_type} '{violation.element_name}')"
            )
        return "\n".join(lines)
