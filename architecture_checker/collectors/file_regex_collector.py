import re
from pathlib import Path
from typing import Set
from .base_collector import BaseCollector
from ..utils.file_utils import get_all_files
from ..utils.ast_utils import parse_file, get_class_names
from ..models.code_element import CodeElement


class FileRegexCollector(BaseCollector):
    def __init__(self, config: dict, project_root: Path):
        self.regex_pattern = config.get("regex", "")
        self.regex = re.compile(self.regex_pattern)
        self.project_root = project_root

    def collect(self) -> Set[CodeElement]:
        all_files = get_all_files(self.project_root)
        collected_elements = set()
        for file_path in all_files:
            relative_path = str(file_path.relative_to(self.project_root))
            if self.regex.match(relative_path):
                tree = parse_file(file_path)
                class_names = get_class_names(tree)
                for class_name in class_names:
                    collected_elements.add(CodeElement(file=file_path, class_name=class_name))
        return collected_elements
