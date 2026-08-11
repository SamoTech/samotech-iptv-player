"""Plugin loader — discovers third-party providers at runtime."""

import importlib
import pkgutil
from pathlib import Path


def load_plugins() -> None:
    pkg_path = str(Path(__file__).parent)
    for _finder, name, _is_pkg in pkgutil.iter_modules([pkg_path]):
        importlib.import_module(f"{__name__}.{name}")
