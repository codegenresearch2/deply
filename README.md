# Deply

**Deply** is a standalone Python tool for enforcing architectural patterns and dependencies in large Python projects. By analyzing code structure and dependencies, this tool ensures that architectural rules are followed, promoting cleaner, more maintainable, and modular codebases.

Inspired by [Deptrac](https://github.com/qossmic/deptrac).

## Features

- **Layer-Based Analysis**: Define project layers and restrict their dependencies to enforce modularity.
- **Dynamic Layer Configuration**: Easily configure collectors for each layer using file patterns and class inheritance.
- **Cross-Layer Dependency Rules**: **TODO** Specify rules to disallow certain layers from accessing others.
- **Extensible and Configurable**: Customize layers and rules for any Python project setup.

## Installation

To install **Deply**, use `pip`:

```bash
pip install deply
```

## Configuration

Before running the tool, create a configuration file (`config.yaml` or similar) that specifies the rules and target files to enforce.

### Collectors

Collectors define how code elements are collected into layers. **Deply** supports several types of collectors:

#### **ClassInheritsCollector**

Collects classes that inherit from a specified base class.

- **Configuration Options**:
    - `type`: `"class_inherits"`
    - `base_class`: The fully qualified name of the base class to match.
    - `exclude_files_regex` (optional): Regular expression to exclude certain files.

**Example**:

```yaml
- type: class_inherits
  base_class: "django.db.models.Model"
```

#### **ClassNameRegexCollector**

Collects classes whose names match a specified regular expression.

- **Configuration Options**:
    - `type`: `"class_name_regex"`
    - `class_name_regex`: Regular expression to match class names.
    - `exclude_files_regex` (optional): Regular expression to exclude certain files.

**Example**:

```yaml
- type: class_name_regex
  class_name_regex: ".*Service$"
  exclude_files_regex: ".*excluded_folder_name.*"
```

#### **DecoratorUsageCollector**

Collects functions or classes that use a specific decorator.

- **Configuration Options**:
    - `type`: `"decorator_usage"`
    - `decorator_name` (optional): The name of the decorator to match exactly.
    - `decorator_regex` (optional): Regular expression to match decorator names.
    - `exclude_files_regex` (optional): Regular expression to exclude certain files.

**Example using `decorator_name`**:

```yaml
- type: decorator_usage
  decorator_name: "login_required"
```

**Example using `decorator_regex`**:

```yaml
- type: decorator_usage
  decorator_regex: "^auth_.*"
```

#### **DirectoryCollector**

Collects code elements from specified directories.

- **Configuration Options**:
    - `type`: `"directory"`
    - `directories`: List of directories (relative to the project root) to include.
    - `recursive` (optional): Whether to search directories recursively (`true` by default).
    - `element_type` (optional): Type of code elements to collect (`"class"`, `"function"`, `"variable"`).
    - `exclude_files_regex` (optional): Regular expression to exclude certain files.

**Example**:

```yaml
- type: directory
  directories:
    - "app1"
    - "utils"
  recursive: true
  element_type: "function"
```

#### **FileRegexCollector**

Collects code elements from files matching a specified regular expression.

- **Configuration Options**:
    - `type`: `"file_regex"`
    - `regex`: Regular expression to match file paths.
    - `element_type` (optional): Type of code elements to collect (`"class"`, `"function"`, `"variable"`).
    - `exclude_files_regex` (optional): Regular expression to exclude certain files.

**Example**:

```yaml
- type: file_regex
  regex: ".*/views_api.py$"
  element_type: "class"
```

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

  - name: views
    collectors:
      - type: file_regex
        regex: ".*/views_api.py"

  - name: utils
    collectors:
      - type: directory
        directories:
          - "utils1" # base_path/utils1
          - "utils2" # base_path/utils2

  - name: services
    collectors:
      - type: class_name_regex
        class_name_regex: ".*Service$"
        exclude_files_regex: ".*excluded_folder_name.*"

  - name: auth_protected
    collectors:
      - type: decorator_usage
        decorator_name: "login_required"

ruleset:
  views:
    disallow:
      - models  # Disallows direct access to models in views
      - utils
```

## Usage

Run the tool from the command line by specifying the project root directory and configuration file:

```bash
python deply.py --config=config.example.yaml
```

### Arguments

- `--config`: Path to the configuration file that defines the rules and target files.

## Sample Output

If violations are found, the tool will output a summary of architectural violations grouped by app, along with details of each violation, such as the file, line number, and violation message.

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