"""Benchmark adapters — auto-discovered on import."""

from __future__ import annotations

import importlib
import pkgutil

from epochx.adapters.base import (
    BenchmarkAdapter,
    get_adapter,
    list_adapters,
    register_adapter,
)

__all__ = [
    "BenchmarkAdapter",
    "register_adapter",
    "get_adapter",
    "list_adapters",
]

# Auto-import every sibling module so that @register_adapter decorators fire.
_pkg_path = __path__
for _importer, _mod_name, _is_pkg in pkgutil.iter_modules(_pkg_path):
    if _mod_name == "base":
        continue
    importlib.import_module(f"{__name__}.{_mod_name}")
