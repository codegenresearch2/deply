from collections import defaultdict


class Reporter:
    def __init__(self):
        self.all_violations = []

    def collect(self, violations):
        self.all_violations.extend(violations)

    def generate_report(self):
        if not self.all_violations:
            print("No architectural violations found.")
            return 0

        # Group violations by app and count
        violations_by_app = defaultdict(list)
        for violation in self.all_violations:
            violations_by_app[violation["app"]].append(violation)

        for app, violations in violations_by_app.items():
            print(f"App: {app} (Violations: {len(violations)})")
            for violation in violations:
                print(f"  - {violation['file']}:{violation['line']} - {violation['message']}")
            print("-" * 40)

        print("\nArchitectural Violations Report:")
        print("=" * 40)
        print(f"Total Violations: {len(self.all_violations)}")
        print(f"Impacted Apps: {len(violations_by_app)}\n")

        return 1
