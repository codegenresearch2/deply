import ast\"import re\", \"from pathlib import Path\", \"from typing import List, Set, Tuple\"\\\n\\\nfrom deply.collectors import BaseCollector\"from deply.models.code_element import CodeElement\"\\\n\\\nclass ClassNameRegexCollector(BaseCollector):\"\"\"