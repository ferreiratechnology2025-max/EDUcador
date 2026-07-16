import importlib
import os
import sys
from pathlib import Path
from typing import Tuple

from .registry import ValidationRegistry


def run(verbose: bool = True) -> Tuple[int, int]:
    project_root = Path(__file__).resolve().parent.parent.parent
    scripts_dir = project_root / "scripts"
    passed = 0
    total = 0

    # 1. All dependencies installed
    total += 1
    deps = ["yaml", "pydantic", "sqlite3"]
    failed_deps = []
    for mod in deps:
        try:
            importlib.import_module(mod)
        except ImportError:
            failed_deps.append(mod)
    if failed_deps:
        if verbose:
            print(f"  FAIL  Missing dependencies: {failed_deps}")
    else:
        passed += 1
        if verbose:
            print(f"  PASS  All dependencies installed")

    # 2. No stale .pyc files
    total += 1
    stale_pyc = 0
    for root, dirs, files in os.walk(project_root):
        for f in files:
            if f.endswith(".pyc"):
                py_file = Path(root) / f.removesuffix(".pyc")
                if not py_file.exists():
                    stale_pyc += 1
    if stale_pyc:
        if verbose:
            print(f"  FAIL  Found {stale_pyc} stale .pyc file(s)")
    else:
        passed += 1
        if verbose:
            print(f"  PASS  No stale .pyc files")

    # 3. No __pycache__ with orphaned entries
    total += 1
    orphaned = 0
    for root, dirs, files in os.walk(project_root):
        if Path(root).name != "__pycache__":
            continue
        py_dir = Path(root).parent
        for f in files:
            if not f.endswith(".pyc"):
                continue
            stem = f.split(".", 1)[0]
            if not (py_dir / f"{stem}.py").exists():
                orphaned += 1
    if orphaned:
        if verbose:
            print(f"  FAIL  Found {orphaned} orphaned __pycache__ entry(ies)")
    else:
        passed += 1
        if verbose:
            print(f"  PASS  No orphaned __pycache__ entries")

    # 4. requirements.txt / pyproject.toml exists
    total += 1
    manifest_found = any(
        (project_root / name).exists()
        for name in ("requirements.txt", "pyproject.toml")
    )
    if manifest_found:
        passed += 1
        if verbose:
            print(f"  PASS  Dependency manifest exists")
    else:
        if verbose:
            print(f"  FAIL  No requirements.txt or pyproject.toml found")

    # 5. Scripts can be imported as modules
    total += 1
    sys.path.insert(0, str(scripts_dir))
    script_modules = sorted(
        f.stem for f in scripts_dir.iterdir()
        if f.suffix == ".py" and not f.name.startswith("_")
    )
    failed_imports = []
    for mod_name in script_modules:
        try:
            importlib.import_module(mod_name)
        except Exception as e:
            failed_imports.append((mod_name, str(e)))
    if failed_imports:
        if verbose:
            for name, err in failed_imports:
                print(f"  FAIL  Cannot import {name}: {err}")
    else:
        passed += 1
        if verbose:
            print(f"  PASS  All scripts importable")

    return passed, total


ValidationRegistry.register("Dependency Validation", run)
