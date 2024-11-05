# Architecture Checker

**Architecture Checker** is a standalone Python tool for enforcing architectural patterns and dependencies in large
Django projects. By analyzing code structure and dependencies, this tool ensures that architectural rules are followed,
promoting cleaner, more maintainable, and modular codebases.

Inspired by https://github.com/qossmic/deptrac

## Features

- **Layer-Based Analysis**: Define project layers and restrict their dependencies to enforce modularity.
- **Dynamic Layer Configuration**: Easily configure collectors for each layer using file patterns and class inheritance.
- **Cross-Layer Dependency Rules** (TODO): Specify rules to disallow certain layers from accessing others.
- **Extensible and Configurable**: Customize layers and rules for any Django project setup.

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
layers:
  - name: models
    collectors:
      - type: class_inherits
        base_class: "django.db.models.Model"

  - name: services
    collectors:
      - type: file_regex
        regex: "^.*/providers.py$"

  - name: views
    collectors:
      - type: file_regex
        regex: ".*/views_api.py"

ruleset:
  views:
    disallow:
      - models  # Disallows direct access to models in views

```

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
/path/to/your_project/your_project/app1/views_api.py:74 - Layer 'views' is not allowed to depend on layer 'models'
```

## Running Tests

To test the tool, use `unittest`:

```bash
python -m unittest discover tests
```

## License

See the [LICENSE](LICENSE) file for details.
