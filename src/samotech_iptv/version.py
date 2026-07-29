"""Single source of truth for the package version.

This file is read by pyproject.toml when the package is installed in
editable mode and importlib.metadata is not yet populated.
"""

#: PEP 440 version string — keep in sync with pyproject.toml.
__version__: str = "0.1.0"

__all__ = ["__version__"]
