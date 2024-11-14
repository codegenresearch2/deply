# Deply

**Deply** is a standalone Python tool for enforcing architectural patterns and dependencies in large
python projects. By analyzing code structure and dependencies, this tool ensures that architectural rules are followed,
promoting cleaner, more maintainable, and modular codebases.

Inspired by https://github.com/qossmic/deptrac

## Features

- **Layer-Based Analysis**: Define project layers and restrict their dependencies to enforce modularity.
- **Dynamic Layer Configuration**: Easily configure collectors for each layer using file patterns and class inheritance.
- **Cross-Layer Dependency Rules** (TODO): Specify rules to disallow certain layers from accessing others.
- **Extensible and Configurable**: Customize layers and rules for any python project setup.

## Installation

To install **Deply**, use `pip`:

```bash
pip install deply
```

## Configuration

Before running the tool, create a configuration file (`config.yaml` or similar) that specifies the rules and target
files to enforce.

### Example Configuration (`config.example.yaml`)

```yaml
paths:
  - /path/to/your/project

exclude_files:
  - ".*\\.venv/.*"

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
python deply.py --config=config.example.yaml
```

### Arguments

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
