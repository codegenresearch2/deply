import ast
import fnmatch
import os

from ..base_rule import BaseRule
from ..utils import get_django_apps, get_django_app_models


class NoCrossAppModelUsageRule(BaseRule):
    def __init__(self, project_root, params):
        super().__init__(project_root, params)
        self.target_files = params.get("target_files", ["*.py"])
        self.exclude_apps = params.get("exclude_apps", [])
        self.apps = [app for app in get_django_apps(project_root) if app not in self.exclude_apps]
        self.app_models = get_django_app_models(project_root, self.apps)

    def run(self):
        for app in self.apps:
            app_path = os.path.join(self.project_root, app)
            for root, _, files in os.walk(app_path):
                for file in files:
                    # Check if the file matches any of the patterns in target_files
                    if any(fnmatch.fnmatch(file, pattern) for pattern in self.target_files):
                        file_path = os.path.join(root, file)
                        self._check_file(file_path, app)

    def _check_file(self, file_path, current_app):
        with open(file_path, "r") as f:
            tree = ast.parse(f.read(), filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_name = self._get_module_name(node)
                if module_name:
                    self._process_import(module_name, node, file_path, current_app)

    def _get_module_name(self, node):
        if isinstance(node, ast.Import):
            return [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                return [node.module]
        return []

    def _process_import(self, module_names, node, file_path, current_app):
        for module_name in module_names:
            for app, models in self.app_models.items():
                if app != current_app and module_name.startswith(f"{app}"):
                    imported_classes = [
                        alias.name for alias in node.names
                    ] if hasattr(node, "names") else []

                    violating_classes = [cls for cls in imported_classes if cls in models]

                    if violating_classes:
                        line_number = node.lineno
                        violation = {
                            "file": file_path,
                            "line": line_number,
                            "app": app,
                            "message": (
                                f"Importing models {violating_classes} from '{app}' in '{current_app}' is not allowed."
                            ),
                        }
                        self.violations.append(violation)
