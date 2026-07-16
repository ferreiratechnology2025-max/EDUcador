"""
ValidationRegistry with explicit module discovery via pkgutil.
Each validator self-registers on import; registry discovers all modules
automatically and verifies against EXPECTED_VALIDATORS manifest.
"""

import pkgutil
import importlib
from pathlib import Path
from typing import Callable, List, Tuple

from .manifest import EXPECTED_VALIDATORS


class ValidationRegistry:
    _validators: List[Tuple[str, Callable[[], Tuple[int, int]]]] = []

    @classmethod
    def register(cls, name: str, fn: Callable[[], Tuple[int, int]]):
        cls._validators.append((name, fn))

    @classmethod
    def discover(cls):
        pkg_path = Path(__file__).parent
        for mod_info in pkgutil.iter_modules([str(pkg_path)]):
            if mod_info.name in ("__init__", "registry", "manifest", "scenarios", "invariants"):
                continue
            importlib.import_module(f"validation.{mod_info.name}")

    @classmethod
    def run_all(cls, verbose: bool = True) -> List[Tuple[str, int, int]]:
        cls.discover()

        registered_names = {n for n, _ in cls._validators}
        expected_set = set(EXPECTED_VALIDATORS)
        missing = expected_set - registered_names
        extra = registered_names - expected_set

        if missing:
            raise RuntimeError(
                f"Validators missing from manifest: {missing}. "
                f"Either add them to manifest.py or fix registration."
            )

        results = []
        for name, fn in cls._validators:
            if verbose:
                print(f"\n{'='*60}\n  {name}\n{'='*60}")
            p, t = fn(verbose=verbose)
            results.append((name, p, t))
        return results

    @classmethod
    def run_selected(cls, names: List[str], verbose: bool = True) -> List[Tuple[str, int, int]]:
        cls.discover()
        results = []
        for vname, fn in cls._validators:
            if not any(n.lower() in vname.lower() for n in names):
                continue
            if verbose:
                print(f"\n{'='*60}\n  {vname}\n{'='*60}")
            p, t = fn(verbose=verbose)
            results.append((vname, p, t))
        return results
