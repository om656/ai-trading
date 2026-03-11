"""
system_tray.py - System tray integration for the AI Trading application.

Provides a persistent tray icon that allows the user to show/hide the main
window and quickly check trading status without opening the full GUI.
"""

import logging
import sys

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PyQt6 imports (optional – app works headlessly if PyQt6 is absent)
# ---------------------------------------------------------------------------
try:
    from PyQt6.QtWidgets import (
        QApplication,
        QMenu,
        QSystemTrayIcon,
    )
    from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
    from PyQt6.QtCore import Qt, QObject, pyqtSignal
    PYQT6_AVAILABLE = True
except ImportError:  # pragma: no cover
    PYQT6_AVAILABLE = False
    logger.warning("PyQt6 not installed – system tray will not be available.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_colored_icon(color: str, size: int = 22) -> "QIcon":
    """Create a simple filled-circle icon with *color* (hex or named colour)."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.end()
    return QIcon(pixmap)


# Tray icon colours by trading state
_STATE_COLORS = {
    "idle":    "#888888",
    "active":  "#00cc44",
    "paused":  "#ffaa00",
    "error":   "#ff3333",
    "paper":   "#3399ff",
}


# ---------------------------------------------------------------------------
# SystemTrayManager
# ---------------------------------------------------------------------------

if PYQT6_AVAILABLE:
    class SystemTrayManager(QObject):
        """Manages the system-tray icon and its context menu.

        Signals
        -------
        show_window_requested
            Emitted when the user asks to restore the main window.
        quit_requested
            Emitted when the user selects *Quit* from the tray menu.
        toggle_trading_requested
            Emitted when the user toggles trading from the tray menu.
        """

        show_window_requested = pyqtSignal()
        quit_requested = pyqtSignal()
        toggle_trading_requested = pyqtSignal()

        def __init__(self, parent: "QObject | None" = None) -> None:
            super().__init__(parent)
            if not QSystemTrayIcon.isSystemTrayAvailable():
                logger.warning("System tray is not available on this desktop.")

            self._state = "idle"
            self._trading_active = False

            self._tray = QSystemTrayIcon(self)
            self._tray.setIcon(_make_colored_icon(_STATE_COLORS["idle"]))
            self._tray.setToolTip("AI Trading System – Idle")

            self._build_menu()

            self._tray.activated.connect(self._on_tray_activated)
            self._tray.show()

        # ------------------------------------------------------------------
        # Public API
        # ------------------------------------------------------------------

        def set_state(self, state: str, tooltip: str = "") -> None:
            """Update the tray icon to reflect *state*.

            Parameters
            ----------
            state:
                One of ``"idle"``, ``"active"``, ``"paused"``, ``"error"``, ``"paper"``.
            tooltip:
                Optional override for the icon tooltip.
            """
            self._state = state
            color = _STATE_COLORS.get(state, _STATE_COLORS["idle"])
            self._tray.setIcon(_make_colored_icon(color))
            if not tooltip:
                tooltip = f"AI Trading System – {state.capitalize()}"
            self._tray.setToolTip(tooltip)

        def show_message(
            self,
            title: str,
            message: str,
            icon: "QSystemTrayIcon.MessageIcon" = None,
            duration_ms: int = 4000,
        ) -> None:
            """Display a tray balloon / notification."""
            if icon is None:
                icon = QSystemTrayIcon.MessageIcon.Information
            self._tray.showMessage(title, message, icon, duration_ms)

        def set_trading_active(self, active: bool) -> None:
            """Sync the *Start / Stop Trading* menu entry with *active*."""
            self._trading_active = active
            label = "⏹  Stop Trading" if active else "▶  Start Trading"
            self._action_toggle.setText(label)
            state = "active" if active else "idle"
            self.set_state(state)

        def set_paper_trading(self, paper: bool) -> None:
            """Reflect paper-trading mode in the tooltip."""
            if paper:
                self.set_state("paper", "AI Trading System – Paper Trading")
            else:
                state = "active" if self._trading_active else "idle"
                self.set_state(state)

        def hide(self) -> None:
            self._tray.hide()

        def show(self) -> None:
            self._tray.show()

        # ------------------------------------------------------------------
        # Private helpers
        # ------------------------------------------------------------------

        def _build_menu(self) -> None:
            menu = QMenu()

            action_show = QAction("🖥  Show Dashboard", self)
            action_show.triggered.connect(self.show_window_requested)
            menu.addAction(action_show)

            menu.addSeparator()

            self._action_toggle = QAction("▶  Start Trading", self)
            self._action_toggle.triggered.connect(self.toggle_trading_requested)
            menu.addAction(self._action_toggle)

            menu.addSeparator()

            action_quit = QAction("✖  Quit", self)
            action_quit.triggered.connect(self.quit_requested)
            menu.addAction(action_quit)

            self._tray.setContextMenu(menu)

        def _on_tray_activated(
            self, reason: "QSystemTrayIcon.ActivationReason"
        ) -> None:
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                self.show_window_requested.emit()

else:  # pragma: no cover
    # Fallback stub so that imports always succeed even without PyQt6
    class SystemTrayManager:  # type: ignore[no-redef]
        """No-op stub used when PyQt6 is not installed."""

        def __init__(self, *args, **kwargs) -> None:
            pass

        def set_state(self, *args, **kwargs) -> None:
            pass

        def show_message(self, *args, **kwargs) -> None:
            pass

        def set_trading_active(self, *args, **kwargs) -> None:
            pass

        def set_paper_trading(self, *args, **kwargs) -> None:
            pass

        def hide(self) -> None:
            pass

        def show(self) -> None:
            pass


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__" and PYQT6_AVAILABLE:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = SystemTrayManager()
    tray.show_window_requested.connect(lambda: print("Show window requested"))
    tray.quit_requested.connect(app.quit)
    tray.toggle_trading_requested.connect(
        lambda: tray.set_trading_active(not tray._trading_active)
    )

    tray.show_message("AI Trading", "System tray is running.")
    sys.exit(app.exec())
