import os
import sys
from pathlib import Path


SOURCE_ROOT = os.environ.get("EVIFLUOR_PYTHON_SOURCE")
if SOURCE_ROOT:
    sys.path.insert(0, SOURCE_ROOT)
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


project = "eviFluor Python API"
author = "HSE AG"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

autosummary_generate = True
autodoc_member_order = "alphabetical"
autodoc_mock_imports = [
    "fastapi",
    "serial",
    "serial.tools",
    "serial.tools.list_ports",
    "uvicorn",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "alabaster"
root_doc = "index"
