"""
portable_version.py - Portable launcher for the AI Trading System.

Enables running the application without a traditional installer by:
  1. Detecting whether all required packages are installed.
  2. Offering to install missing packages into a local ``venv/`` next to this file.
  3. Launching ``gui_app.py`` (or ``ai-trading.exe`` if it has been built).

Usage
-----
    python portable_version.py            # interactive mode
    python portable_version.py --auto     # auto-install deps and launch
    python portable_version.py --check    # dependency check only (no launch)

The script is designed to be bundled alongside the source files so that users
who have *any* Python ≥ 3.9 can run the full application without a system-wide
install.
"""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APP_DIR = Path(__file__).parent.resolve()
MAIN_SCRIPT = APP_DIR / "gui_app.py"
BUILT_EXE = APP_DIR / "dist" / "ai-trading.exe"
VENV_DIR = APP_DIR / "venv"
PYTHON_MIN = (3, 9)

# Required packages: (import_name, pip_install_name)
REQUIRED_PACKAGES: list[tuple[str, str]] = [
    ("PyQt6", "PyQt6"),
    ("cryptography", "cryptography"),
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("matplotlib", "matplotlib"),
    ("ccxt", "ccxt"),
    ("psutil", "psutil"),
]

OPTIONAL_PACKAGES: list[tuple[str, str]] = [
    ("sklearn", "scikit-learn"),
    ("nltk", "nltk"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_python() -> bool:
    """Return True if the running Python satisfies the minimum version."""
    return sys.version_info >= PYTHON_MIN


def _is_importable(module_name: str) -> bool:
    """Return True if *module_name* can be imported."""
    spec = importlib.util.find_spec(module_name)  # type: ignore[attr-defined]
    return spec is not None


def _check_dependencies() -> tuple[list[str], list[str]]:
    """Return (missing_required, missing_optional)."""
    missing_req = [
        pip_name
        for import_name, pip_name in REQUIRED_PACKAGES
        if not _is_importable(import_name)
    ]
    missing_opt = [
        pip_name
        for import_name, pip_name in OPTIONAL_PACKAGES
        if not _is_importable(import_name)
    ]
    return missing_req, missing_opt


def _pip_install(packages: list[str], venv: bool = False) -> bool:
    """Install *packages* via pip.  Returns True on success."""
    python = _venv_python() if venv and VENV_DIR.exists() else sys.executable
    cmd = [str(python), "-m", "pip", "install", "--quiet", "--upgrade"] + packages
    print(f"  Installing: {', '.join(packages)} …")
    result = subprocess.run(cmd, check=False)
    return result.returncode == 0


def _create_venv() -> bool:
    """Create a virtual environment in *VENV_DIR*.  Returns True on success."""
    print(f"  Creating virtual environment at {VENV_DIR} …")
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)], check=False
    )
    return result.returncode == 0


def _venv_python() -> Path:
    """Return the path to the Python executable inside the venv."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _launch_app() -> None:
    """Launch the GUI application (EXE if available, else Python script)."""
    if BUILT_EXE.exists():
        print(f"\n🚀  Launching {BUILT_EXE} …")
        os.startfile(str(BUILT_EXE))  # type: ignore[attr-defined]
        return

    if not MAIN_SCRIPT.exists():
        print(f"\n✗  Could not find {MAIN_SCRIPT}.")
        sys.exit(1)

    python = _venv_python() if VENV_DIR.exists() else Path(sys.executable)
    print(f"\n🚀  Launching {MAIN_SCRIPT} …")
    # Replace current process (exec) so we don't leave a zombie launcher.
    if sys.platform == "win32":
        os.execv(str(python), [str(python), str(MAIN_SCRIPT)])
    else:
        os.execv(str(python), [str(python), str(MAIN_SCRIPT)])


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------

def _prompt_yes_no(question: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        answer = input(f"{question} {suffix}: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please enter 'y' or 'n'.")


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def run(auto: bool = False, check_only: bool = False) -> None:
    print("=" * 60)
    print("  AI Trading System – Portable Launcher")
    print("=" * 60)

    # Python version check
    if not _check_python():
        v = ".".join(str(x) for x in PYTHON_MIN)
        print(f"\n✗  Python {v}+ is required. Current: {sys.version}")
        sys.exit(1)
    print(f"\n✔  Python {sys.version.split()[0]} detected.")

    # Dependency check
    print("\n🔍  Checking dependencies …")
    missing_req, missing_opt = _check_dependencies()

    if not missing_req and not missing_opt:
        print("  All required packages are installed.")
    else:
        if missing_req:
            print(f"  ✗  Missing required: {', '.join(missing_req)}")
        if missing_opt:
            print(f"  ℹ  Missing optional: {', '.join(missing_opt)}")

    if check_only:
        sys.exit(0 if not missing_req else 1)

    # Install missing packages
    if missing_req:
        if auto or _prompt_yes_no("\nInstall missing required packages?"):
            # Prefer a local venv to avoid polluting the system Python
            if not VENV_DIR.exists():
                if auto or _prompt_yes_no(
                    "Create a local virtual environment (recommended)?", default=True
                ):
                    if not _create_venv():
                        print("  ✗  Venv creation failed. Falling back to system pip.")

            ok = _pip_install(missing_req, venv=VENV_DIR.exists())
            if not ok:
                print("\n✗  Package installation failed. Please install manually:")
                print(f"   pip install {' '.join(missing_req)}")
                sys.exit(1)
            print("  ✔  Required packages installed.")
        else:
            print("\nCannot launch without required packages. Exiting.")
            sys.exit(1)

    if missing_opt:
        if auto or _prompt_yes_no("\nInstall optional packages for extra features?", default=False):
            _pip_install(missing_opt, venv=VENV_DIR.exists())

    # Launch
    _launch_app()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Portable launcher for the AI Trading System."
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically install missing dependencies without prompting.",
    )
    parser.add_argument(
        "--check",
        dest="check_only",
        action="store_true",
        help="Only check dependencies, do not launch the application.",
    )
    args = parser.parse_args()
    run(auto=args.auto, check_only=args.check_only)


if __name__ == "__main__":
    main()
