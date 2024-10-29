import ast
import os


def get_django_apps(project_root):
    apps = []
    for item in os.listdir(project_root):
        item_path = os.path.join(project_root, item)

        if os.path.isdir(item_path):
            # Check for a Django app structure: presence of '__init__.py'
            if os.path.isfile(os.path.join(item_path, '__init__.py')):
                apps.append(item)

    return apps


def _is_django_model_like_class(class_def):
    has_model_base = any(
        isinstance(base, ast.Attribute) and base.attr == "Model" and getattr(base.value, "id", None) == "models"
        for base in class_def.bases
    )

    return has_model_base


def get_django_app_models(project_root, apps):
    app_models = {}
    for app in apps:
        models_in_app = []
        app_path = os.path.join(project_root, app)

        for root, _, files in os.walk(app_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r") as f:
                        tree = ast.parse(f.read(), filename=file_path)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef) and _is_django_model_like_class(node):
                            models_in_app.append(node.name)

        if models_in_app:
            app_models[app] = models_in_app

    return app_models
