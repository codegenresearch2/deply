# Architecture Checker

**Architecture Checker** is a Python tool to enforce architectural patterns in Django projects, ensuring modularity,
maintainability, and compliance with predefined architectural rules.

## Installation

To install **Architecture Checker**, use `pip`:

```bash
pip install architecture_checker
```

## Configuration

Before running the tool, create a configuration file (`config.yaml` or similar) that specifies the rules and target
files to enforce.

### Example Configuration (`config.example.yaml`)

```yaml
rules:
  - name: NoCrossAppModelUsageRule
    enabled: true
    params:
      target_files: [ "*.py" ]
      exclude_apps: [ "admin", "auth" ]
```

- **rules**: A list of architectural rules to enforce.
    - **name**: The class name of the rule (e.g., `NoCrossAppModelUsageRule`).
    - **enabled**: Boolean indicating if the rule should be active.
    - **params**: Rule-specific parameters.
        - **target_files**: Specifies files to check using wildcard patterns (e.g., `["*.py"]` for all Python files).
        - **exclude_apps**: Apps to exclude from this rule.

## Usage

Run the tool from the command line by specifying the project root directory and configuration file:

```bash
python run_architecture_checker.py --project_root='/path/to/your_project' --config=config.example.yaml
```

### Arguments

- `--project_root`: The path to the root of the Django project where apps are located.
- `--config`: Path to the configuration file that defines the rules and target files.

## Sample Output

If violations are found, the tool will output a summary of architectural violations grouped by app, along with details
of each violation, such as the file, line number, and violation message.

```plaintext

App: app1 (Violations: 2)
  - app1/views.py:15 - Importing models ['SomeModel'] from 'app2' in 'app1' is not allowed.
  - app1/tasks.py:42 - Importing models ['AnotherModel'] from 'app2' in 'app1' is not allowed.
----------------------------------------

App: app2 (Violations: 1)
  - app2/providers.py:20 - Importing models ['ThirdModel'] from 'app3' in 'app2' is not allowed.
----------------------------------------


Architectural Violations Report:
========================================
Total Violations: 3
Impacted Apps: 2

```

If no violations are detected:

```plaintext
No architectural violations found.
```

## Running Tests

To test the tool, use `unittest`:

```bash
python -m unittest discover tests
```

## License

See the [LICENSE](LICENSE) file for details.
