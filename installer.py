"""
installer.py - Windows installer script for the AI Trading System.

Creates a fully configured Windows installation including:
  • Copying application files to Program Files
  • Desktop and Start Menu shortcuts
  • Windows registry entries for Add/Remove Programs
  • Optional auto-start registry entry
  • Uninstaller

Run with administrator privileges for a system-wide install, or without
for a per-user install into %LOCALAPPDATA%.

Usage
-----
    python installer.py install   [--system]  [--autostart]
    python installer.py uninstall [--system]

Note
----
On non-Windows platforms this script prints an informative message and exits.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

WINDOWS = sys.platform == "win32"

APP_NAME = "AI Trading System"
APP_VERSION = "1.0.0"
APP_EXE = "ai-trading.exe"
PUBLISHER = "AITrading"
REGISTRY_UNINSTALL_KEY = (
    r"Software\Microsoft\Windows\CurrentVersion\Uninstall\AITrading"
)

# Files / folders to copy into the installation directory
INSTALL_FILES = [
    "gui_app.py",
    "app_config.py",
    "system_tray.py",
    "advanced_nlp_sentiment.py",
    "main_advanced_trading_system.py",
    "requirements.txt",
]
INSTALL_DIRS: list[str] = ["src"]


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _install_dir(system_wide: bool) -> Path:
    if system_wide:
        base = os.environ.get("PROGRAMFILES", r"C:\Program Files")
    else:
        base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    return Path(base) / APP_NAME


def _start_menu_dir(system_wide: bool) -> Path:
    if system_wide:
        base = os.environ.get("ALLUSERSPROFILE", r"C:\ProgramData")
    else:
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    return Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME


def _desktop_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


# ---------------------------------------------------------------------------
# Shortcut creation (Windows only, via win32com or winshell)
# ---------------------------------------------------------------------------

def _create_shortcut(target: Path, shortcut_path: Path, description: str = "") -> bool:
    """Create a Windows .lnk shortcut.  Returns True on success."""
    if not WINDOWS:
        return False
    try:
        import win32com.client  # type: ignore
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.TargetPath = str(target)
        shortcut.WorkingDirectory = str(target.parent)
        shortcut.Description = description
        shortcut.save()
        return True
    except ImportError:
        print(
            "  ⚠  pywin32 not installed – cannot create .lnk shortcut.\n"
            "     Install with: pip install pywin32"
        )
        return False
    except Exception as exc:
        print(f"  ⚠  Shortcut creation failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# Registry helpers (Windows only)
# ---------------------------------------------------------------------------

def _reg_write_uninstall(install_dir: Path, uninstaller_path: Path) -> None:
    if not WINDOWS:
        return
    try:
        import winreg  # type: ignore
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_UNINSTALL_KEY) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
            winreg.SetValueEx(
                key, "UninstallString", 0, winreg.REG_SZ,
                f'"{sys.executable}" "{uninstaller_path}" uninstall'
            )
            winreg.SetValueEx(
                key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir)
            )
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        print("  ✔  Registered in Add/Remove Programs.")
    except Exception as exc:
        print(f"  ⚠  Registry write failed: {exc}")


def _reg_remove_uninstall() -> None:
    if not WINDOWS:
        return
    try:
        import winreg  # type: ignore
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_UNINSTALL_KEY)
        print("  ✔  Removed from Add/Remove Programs.")
    except FileNotFoundError:
        pass
    except Exception as exc:
        print(f"  ⚠  Registry removal failed: {exc}")


def _reg_set_autostart(enabled: bool, exe_path: Path) -> None:
    if not WINDOWS:
        return
    try:
        import winreg  # type: ignore
        run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
                print("  ✔  Added to Windows startup.")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
    except Exception as exc:
        print(f"  ⚠  Auto-start registry update failed: {exc}")


# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

def install(system_wide: bool = False, autostart: bool = False) -> None:
    if not WINDOWS:
        print("ℹ  This installer is designed for Windows.")
        print("   On Linux/macOS, run gui_app.py directly: python gui_app.py")
        return

    install_dir = _install_dir(system_wide)
    print(f"\n📂  Installing to {install_dir} …")
    install_dir.mkdir(parents=True, exist_ok=True)

    src_root = Path(__file__).parent.resolve()

    # Copy Python source files
    for filename in INSTALL_FILES:
        src = src_root / filename
        if src.exists():
            shutil.copy2(src, install_dir / filename)
            print(f"  Copied {filename}")
        else:
            print(f"  ⚠  Not found, skipping: {filename}")

    # Copy directories
    for dirname in INSTALL_DIRS:
        src = src_root / dirname
        if src.exists():
            dest = install_dir / dirname
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(f"  Copied {dirname}/")

    # Copy this installer for the uninstaller
    uninstaller = install_dir / "uninstall.py"
    shutil.copy2(__file__, uninstaller)

    # Determine what to launch: EXE if built, else Python script
    exe_path = install_dir / APP_EXE
    launcher = exe_path if exe_path.exists() else install_dir / "gui_app.py"

    # Desktop shortcut
    desktop_lnk = _desktop_dir() / f"{APP_NAME}.lnk"
    if _create_shortcut(launcher, desktop_lnk, f"Launch {APP_NAME}"):
        print(f"  ✔  Desktop shortcut: {desktop_lnk}")

    # Start Menu
    start_dir = _start_menu_dir(system_wide)
    start_dir.mkdir(parents=True, exist_ok=True)
    start_lnk = start_dir / f"{APP_NAME}.lnk"
    if _create_shortcut(launcher, start_lnk, f"Launch {APP_NAME}"):
        print(f"  ✔  Start Menu entry:  {start_lnk}")
    # Uninstall shortcut in Start Menu
    uninst_lnk = start_dir / f"Uninstall {APP_NAME}.lnk"
    _create_shortcut(
        Path(sys.executable),
        uninst_lnk,
        f"Uninstall {APP_NAME}",
    )

    # Registry
    _reg_write_uninstall(install_dir, uninstaller)

    # Auto-start
    if autostart:
        _reg_set_autostart(True, launcher)

    print(f"\n✅  Installation complete!\n   Run: {launcher}")


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

def uninstall(system_wide: bool = False) -> None:
    if not WINDOWS:
        print("ℹ  Uninstaller is Windows-only.")
        return

    install_dir = _install_dir(system_wide)
    print(f"\n🗑  Uninstalling {APP_NAME} from {install_dir} …")

    # Remove files
    if install_dir.exists():
        shutil.rmtree(install_dir)
        print(f"  Removed {install_dir}")

    # Remove shortcuts
    desktop_lnk = _desktop_dir() / f"{APP_NAME}.lnk"
    if desktop_lnk.exists():
        desktop_lnk.unlink()
        print(f"  Removed desktop shortcut.")

    start_dir = _start_menu_dir(system_wide)
    if start_dir.exists():
        shutil.rmtree(start_dir)
        print("  Removed Start Menu entry.")

    # Registry
    _reg_remove_uninstall()
    _reg_set_autostart(False, Path(""))

    print(f"\n✅  {APP_NAME} has been uninstalled.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} Windows Installer"
    )
    sub = parser.add_subparsers(dest="command")

    inst_p = sub.add_parser("install", help="Install the application.")
    inst_p.add_argument(
        "--system",
        action="store_true",
        help="Install system-wide (requires administrator rights).",
    )
    inst_p.add_argument(
        "--autostart",
        action="store_true",
        help="Launch automatically when Windows starts.",
    )

    uninst_p = sub.add_parser("uninstall", help="Uninstall the application.")
    uninst_p.add_argument(
        "--system",
        action="store_true",
        help="Uninstall system-wide installation.",
    )

    args = parser.parse_args()

    print("=" * 60)
    print(f"  {APP_NAME} – Installer v{APP_VERSION}")
    print("=" * 60)

    if args.command == "install":
        install(system_wide=args.system, autostart=args.autostart)
    elif args.command == "uninstall":
        uninstall(system_wide=args.system)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
