"""
build_exe.py - PyInstaller build script for creating the AI Trading EXE.

Usage
-----
    python build_exe.py              # default: one-file EXE
    python build_exe.py --onedir     # one-directory build (faster startup)
    python build_exe.py --debug      # include debug console
    python build_exe.py --clean      # remove previous build artifacts first

The resulting EXE is placed in the ``dist/`` folder.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Build configuration
# ---------------------------------------------------------------------------
APP_NAME = "ai-trading"
ENTRY_SCRIPT = "gui_app.py"
ICON_FILE = "assets/icon.ico"          # optional – set to None to skip
VERSION = "1.0.0"

# Extra data files to bundle: list of (src, dest_folder_in_bundle)
EXTRA_DATA: list[tuple[str, str]] = [
    # ("assets/",         "assets/"),
    # ("models/",         "models/"),
]

# Hidden imports that PyInstaller may miss
HIDDEN_IMPORTS: list[str] = [
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "matplotlib.backends.backend_qtagg",
    "cryptography",
    "ccxt",
    "numpy",
    "pandas",
    "sklearn",
    "psutil",
]

# Runtime hooks (optional)
RUNTIME_HOOKS: list[str] = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str]) -> None:
    """Run *cmd* and raise on failure."""
    print(f"\n▶  {' '.join(cmd)}\n")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"\n✗  Command failed with exit code {result.returncode}.")
        sys.exit(result.returncode)


def _ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller not found – installing …")
        _run([sys.executable, "-m", "pip", "install", "pyinstaller"])


def _clean() -> None:
    for folder in ("build", f"dist/{APP_NAME}", "__pycache__"):
        path = Path(folder)
        if path.exists():
            shutil.rmtree(path)
            print(f"  Removed {path}")
    spec_file = Path(f"{APP_NAME}.spec")
    if spec_file.exists():
        spec_file.unlink()
        print(f"  Removed {spec_file}")


def _build(one_dir: bool, debug: bool) -> None:
    cmd = [sys.executable, "-m", "PyInstaller"]

    if not one_dir:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    cmd += ["--name", APP_NAME]

    if not debug:
        cmd += ["--windowed"]          # hide console window
    else:
        cmd += ["--console"]

    icon_path = Path(ICON_FILE)
    if icon_path.exists():
        cmd += ["--icon", str(icon_path)]
    else:
        print(f"  ⚠  Icon file not found ({ICON_FILE}) – skipping icon.")

    for src, dest in EXTRA_DATA:
        sep = ";" if sys.platform == "win32" else ":"
        cmd += ["--add-data", f"{src}{sep}{dest}"]

    for module in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", module]

    for hook in RUNTIME_HOOKS:
        cmd += ["--runtime-hook", hook]

    # Metadata
    cmd += [
        "--version-file", _write_version_file(),
    ] if sys.platform == "win32" else []

    cmd.append(ENTRY_SCRIPT)
    _run(cmd)


def _write_version_file() -> str:
    """Write a Windows version-info file for PyInstaller and return its path."""
    content = f"""\
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({VERSION.replace('.', ', ')}, 0),
    prodvers=({VERSION.replace('.', ', ')}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'AITrading'),
         StringStruct(u'FileDescription', u'AI Trading System'),
         StringStruct(u'FileVersion', u'{VERSION}'),
         StringStruct(u'InternalName', u'{APP_NAME}'),
         StringStruct(u'LegalCopyright', u'MIT Licence'),
         StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
         StringStruct(u'ProductName', u'AI Trading System'),
         StringStruct(u'ProductVersion', u'{VERSION}')])]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    path = Path("version_info.txt")
    path.write_text(content, encoding="utf-8")
    return str(path)


def _post_build(one_dir: bool) -> None:
    if one_dir:
        exe = Path("dist") / APP_NAME / f"{APP_NAME}.exe"
    else:
        exe = Path("dist") / f"{APP_NAME}.exe"

    if exe.exists():
        size_mb = exe.stat().st_size / (1024 * 1024)
        print(f"\n✔  Build successful!")
        print(f"   Output : {exe.resolve()}")
        print(f"   Size   : {size_mb:.1f} MB")
    else:
        print("\n✗  EXE not found – build may have failed.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build ai-trading.exe using PyInstaller."
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Create a one-directory build instead of a single-file EXE.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Include a console window for debug output.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove previous build artifacts before building.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  AI Trading System – EXE Builder")
    print("=" * 60)

    _ensure_pyinstaller()

    if args.clean:
        print("\n🧹  Cleaning previous build …")
        _clean()

    print(f"\n📦  Building {'one-directory' if args.onedir else 'single-file'} EXE …")
    _build(one_dir=args.onedir, debug=args.debug)
    _post_build(one_dir=args.onedir)


if __name__ == "__main__":
    main()
