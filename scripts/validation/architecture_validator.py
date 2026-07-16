import ast
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from .registry import ValidationRegistry


ALLOWED_PEDAGOGY_IMPORTS_FOR_LEARNING = {
    "pedagogy.models",
    "pedagogy.models.context",
    "pedagogy.models.evidence",
    "pedagogy.models.probe",
    "pedagogy.models.action",
    "pedagogy.probes.repository",
    "pedagogy.composer",
    "pedagogy.composer.instruction_composer",
}

FORBIDDEN_PEDAGOGY_PREFIXES = {
    "pedagogy.memory",
    "pedagogy.extractors",
    "pedagogy.planner",
    "pedagogy.knowledge",
    "pedagogy.probes.evaluator",
}

EXEMPT_LEARNING_FILES = {
    "runtime.py",
    "factory.py",      # DT-001: Factory needs direct access to construct Runtime. Fix: add Runtime.build() factory method.
    "engine_inspector.py",  # DT-002: Inspector needs direct access for diagnostics. Fix: refactor to accept Runtime.
}


def _is_pedagogy_import(node_text: str) -> bool:
    return node_text.startswith("pedagogy") or node_text.startswith("src.pedagogy")


def _get_imported_modules(tree: ast.AST) -> List[str]:
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                level = node.level or 0
                if level == 0:
                    modules.append(node.module)
    return modules


def check_pedagogical_engine_not_import_event_store(
    src_root: Path, verbose: bool
) -> bool:
    engine_path = (
        src_root / "learning" / "engine" / "pedagogical_engine.py"
    )
    if not engine_path.exists():
        if verbose:
            print("  FAIL  pedagogical_engine.py not found")
        return False

    with open(engine_path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(engine_path))

    modules = _get_imported_modules(tree)
    for mod in modules:
        if "event_store" in mod.lower():
            if verbose:
                print(
                    "  FAIL  PedagogicalEngine directly imports EventStore "
                    f"({mod})"
                )
            return False

    if verbose:
        print("  PASS  PedagogicalEngine does not directly import EventStore")
    return True


def check_strategy_executor_not_import_event_store(
    src_root: Path, verbose: bool
) -> bool:
    executor_path = (
        src_root / "learning" / "executor" / "strategy_executor.py"
    )
    if not executor_path.exists():
        if verbose:
            print("  FAIL  strategy_executor.py not found")
        return False

    with open(executor_path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(executor_path))

    modules = _get_imported_modules(tree)
    for mod in modules:
        if "event_store" in mod.lower():
            if verbose:
                print(
                    "  FAIL  StrategyExecutor directly imports EventStore "
                    f"({mod})"
                )
            return False

    if verbose:
        print("  PASS  StrategyExecutor does not import EventStore")
    return True


def check_domain_no_pedagogy_memory(src_root: Path, verbose: bool) -> bool:
    domain_dir = src_root / "learning" / "domain"
    if not domain_dir.is_dir():
        if verbose:
            print("  FAIL  src/learning/domain/ not found")
        return False

    violations = []
    for root, _dirs, files in os.walk(domain_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            filepath = Path(root) / f
            with open(filepath, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=str(filepath))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(
                            "pedagogy"
                        ) or alias.name.startswith("src.pedagogy"):
                            violations.append((filepath.name, alias.name))
                elif isinstance(node, ast.ImportFrom):
                    if node.module and (
                        node.module.startswith("pedagogy")
                        or node.module.startswith("src.pedagogy")
                    ):
                        violations.append((filepath.name, node.module))

    if violations:
        if verbose:
            for fname, mod in violations:
                print(
                    f"  FAIL  {fname} imports from pedagogy/memory: {mod}"
                )
        return False

    if verbose:
        print("  PASS  Domain classes do not import from pedagogy/memory")
    return True


def check_circular_imports(src_root: str, verbose: bool) -> bool:
    cmd = [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, 'src'); from learning import engine",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=src_root,
    )
    if result.returncode != 0:
        if verbose:
            stderr = result.stderr.strip()
            print(
                "  FAIL  Circular import detected: "
                f"{stderr.split(chr(10))[-1]}"
            )
        return False

    if verbose:
        print("  PASS  No circular imports")
    return True


def get_top_level_package(mod_path: str) -> str:
    parts = mod_path.split(".")
    if parts[0] == "src":
        return ".".join(parts[:3])
    return parts[0]


def check_import_stability(src_root: Path, verbose: bool) -> bool:
    learning_dir = src_root / "learning"
    violations = []

    for root, _dirs, files in os.walk(learning_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            rel_dir = Path(root).relative_to(src_root)
            if f in EXEMPT_LEARNING_FILES:
                continue

            filepath = Path(root) / f
            with open(filepath, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=str(filepath))

            for node in ast.walk(tree):
                imports_to_check = []
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_to_check.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports_to_check.append(node.module)

                for mod in imports_to_check:
                    if not _is_pedagogy_import(mod):
                        continue

                    if mod.startswith("src."):
                        rel_mod = mod[4:]
                    else:
                        rel_mod = mod

                    if rel_mod in ALLOWED_PEDAGOGY_IMPORTS_FOR_LEARNING:
                        continue

                    is_forbidden = any(
                        rel_mod.startswith(prefix)
                        for prefix in FORBIDDEN_PEDAGOGY_PREFIXES
                    )
                    if is_forbidden:
                        violations.append(
                            (str(rel_dir / f), mod)
                        )

    if violations:
        if verbose:
            for fpath, mod in violations:
                print(
                    f"  FAIL  {fpath} directly imports {mod} "
                    "(should go through runtime.py)"
                )
        return False

    if verbose:
        print(
            "  PASS  All learning-layer pedagogy imports go through "
            "runtime.py or are allowed exceptions"
        )
    return True


def run(verbose: bool = True) -> Tuple[int, int]:
    project_root = Path(__file__).resolve().parent.parent.parent
    src_root = project_root / "src"
    passed = 0
    total = 5

    # 1. PedagogicalEngine -> EventStore direct import
    if check_pedagogical_engine_not_import_event_store(src_root, verbose):
        passed += 1

    # 2. StrategyExecutor -> EventStore direct import
    if check_strategy_executor_not_import_event_store(src_root, verbose):
        passed += 1

    # 3. Domain classes -> pedagogy/memory
    if check_domain_no_pedagogy_memory(src_root, verbose):
        passed += 1

    # 4. Circular imports
    if check_circular_imports(str(project_root), verbose):
        passed += 1

    # 5. Import stability
    if check_import_stability(src_root, verbose):
        passed += 1

    return passed, total


ValidationRegistry.register("Architecture Validation", run)
