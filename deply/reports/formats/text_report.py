from collections import defaultdict
from ...models.violation import Violation


class TextReport:
    def __init__(self, violations: list[Violation]):
        self.violations = violations

    def generate(self) -> str:
        grouped_violations = self._group_violations_by_type()
        lines = []
        for violation_type, type_violations in grouped_violations.items():
            lines.append(violation_type)
            sorted_violations = sorted(type_violations, key=lambda v: (v.file, v.line, v.column))
            for violation in sorted_violations:
                lines.append(f"{violation.file}:{violation.line}:{violation.column} - {violation.message}")
            lines.append("")

        for violation_type, type_violations in grouped_violations.items():
            lines.append(f"{violation_type}: {len(type_violations)}")

        total_count = len(self.violations)
        lines.append(f"\nTotal Violations: {total_count}")

        return "\n".join(lines)

    def _group_violations_by_type(self) -> dict[str, list[Violation]]:
        grouped = defaultdict(list)
        for violation in self.violations:
            grouped[violation.violation_type].append(violation)
        return dict(grouped)
