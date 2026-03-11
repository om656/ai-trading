"""
gui_app.py - Main PyQt6 GUI application for the AI Trading System.

Architecture
------------
MainWindow (QMainWindow)
├── QTabWidget
│   ├── DashboardTab   – portfolio value, P&L, win rate, activity log, charts
│   ├── TradingTab     – start/stop, paper mode, manual trades, positions
│   ├── AnalysisTab    – sentiment scores, AI signals, risk warnings
│   ├── SettingsTab    – API keys, trading params, model/exchange selection
│   └── StatusTab      – system health, CPU/GPU, logs
├── TradingEngine      – background QThread driving all trading logic
└── SystemTrayManager  – tray icon with show/quit/toggle actions
"""

from __future__ import annotations

import datetime
import logging
import random
import sys
import time
from typing import List, Optional

# ---------------------------------------------------------------------------
# PyQt6
# ---------------------------------------------------------------------------
try:
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFormLayout,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSlider,
        QSpinBox,
        QSplitter,
        QStatusBar,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
        QDoubleSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QProgressBar,
    )
    from PyQt6.QtCore import (
        Qt,
        QThread,
        QTimer,
        pyqtSignal,
        QObject,
    )
    from PyQt6.QtGui import (
        QColor,
        QFont,
        QPalette,
        QIcon,
        QPixmap,
        QPainter,
    )
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False

# ---------------------------------------------------------------------------
# Optional matplotlib for performance charts
# ---------------------------------------------------------------------------
try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# ---------------------------------------------------------------------------
# Optional psutil for system monitoring
# ---------------------------------------------------------------------------
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ---------------------------------------------------------------------------
# Local modules
# ---------------------------------------------------------------------------
from app_config import config
from system_tray import SystemTrayManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dark theme stylesheet
# ---------------------------------------------------------------------------
DARK_STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #2d2d44;
    background-color: #16213e;
}
QTabBar::tab {
    background-color: #0f3460;
    color: #aaaaaa;
    padding: 8px 18px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 100px;
}
QTabBar::tab:selected {
    background-color: #e94560;
    color: #ffffff;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background-color: #1a4a80;
}
QPushButton {
    background-color: #0f3460;
    color: #ffffff;
    border: 1px solid #1a5276;
    border-radius: 5px;
    padding: 7px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1a5276;
}
QPushButton:pressed {
    background-color: #0d2840;
}
QPushButton#startBtn {
    background-color: #1e8449;
    border-color: #27ae60;
    font-size: 14px;
    padding: 10px 24px;
}
QPushButton#startBtn:hover { background-color: #27ae60; }
QPushButton#stopBtn {
    background-color: #922b21;
    border-color: #e74c3c;
    font-size: 14px;
    padding: 10px 24px;
}
QPushButton#stopBtn:hover { background-color: #e74c3c; }
QPushButton#emergencyBtn {
    background-color: #6e2121;
    border-color: #ff0000;
    color: #ff6666;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#emergencyBtn:hover { background-color: #a93226; }
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #2d2d44;
    border-radius: 4px;
    padding: 4px 8px;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #e94560;
}
QGroupBox {
    border: 1px solid #2d2d44;
    border-radius: 6px;
    margin-top: 14px;
    padding: 10px;
    color: #aab7d4;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}
QLabel#metricValue {
    font-size: 22px;
    font-weight: bold;
    color: #e94560;
}
QLabel#metricLabel {
    font-size: 11px;
    color: #888888;
}
QLabel#signalBull { color: #27ae60; font-weight: bold; }
QLabel#signalBear { color: #e74c3c; font-weight: bold; }
QLabel#signalNeutral { color: #f39c12; font-weight: bold; }
QTableWidget {
    background-color: #0f3460;
    color: #e0e0e0;
    gridline-color: #2d2d44;
    selection-background-color: #e94560;
}
QHeaderView::section {
    background-color: #0d2840;
    color: #aab7d4;
    padding: 4px;
    border: 1px solid #2d2d44;
    font-weight: bold;
}
QScrollBar:vertical {
    background: #1a1a2e;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #0f3460;
    border-radius: 5px;
}
QStatusBar {
    background-color: #0d2840;
    color: #aaaaaa;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #2d2d44;
    border-radius: 3px;
    background-color: #0f3460;
}
QCheckBox::indicator:checked {
    background-color: #e94560;
    border-color: #e94560;
}
QProgressBar {
    border: 1px solid #2d2d44;
    border-radius: 4px;
    background-color: #0f3460;
    text-align: center;
    color: #e0e0e0;
}
QProgressBar::chunk { background-color: #e94560; border-radius: 3px; }
QSlider::groove:horizontal {
    height: 4px;
    background: #2d2d44;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #e94560;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
"""

LIGHT_STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #f5f5f5;
    color: #212121;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}
"""

# ---------------------------------------------------------------------------
# Simulated trading engine (runs in a background thread)
# ---------------------------------------------------------------------------

class TradingEngine(QObject if PYQT6_AVAILABLE else object):
    """Lightweight simulated trading engine for UI demonstration.

    In production this would wrap real market-data and order-execution logic.
    """

    if PYQT6_AVAILABLE:
        tick = pyqtSignal(dict)          # periodic market update
        trade_executed = pyqtSignal(dict)
        alert = pyqtSignal(str, str)     # title, message

    def __init__(self, parent: Optional[QObject] = None) -> None:
        if PYQT6_AVAILABLE:
            super().__init__(parent)
        self._running = False
        self._paper = True

        # Simulated state
        self._portfolio_value = 10_000.0
        self._daily_pnl = 0.0
        self._wins = 0
        self._trades = 0
        self._positions: List[dict] = []

    # ------------------------------------------------------------------
    # QThread slot
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main loop – called from a QThread."""
        self._running = True
        logger.info("Trading engine started (paper=%s).", self._paper)
        while self._running:
            time.sleep(2)
            self._simulate_tick()

    def stop(self) -> None:
        self._running = False

    def set_paper(self, paper: bool) -> None:
        self._paper = paper

    # ------------------------------------------------------------------
    # Internal simulation
    # ------------------------------------------------------------------

    def _simulate_tick(self) -> None:
        change = random.uniform(-50, 60)
        self._portfolio_value += change
        self._daily_pnl += change

        signal = random.choice(["BUY", "SELL", "HOLD", "HOLD", "HOLD"])
        sentiment = round(random.uniform(-1, 1), 3)
        confidence = round(random.uniform(0.5, 0.99), 2)

        if signal in ("BUY", "SELL") and random.random() > 0.7:
            trade = {
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "symbol": random.choice(["BTC/USDT", "ETH/USDT"]),
                "side": signal,
                "qty": round(random.uniform(0.001, 0.05), 4),
                "price": round(random.uniform(25_000, 65_000), 2),
                "paper": self._paper,
            }
            self._trades += 1
            if random.random() > 0.45:
                self._wins += 1
            if PYQT6_AVAILABLE:
                self.trade_executed.emit(trade)

        win_rate = (self._wins / self._trades * 100) if self._trades else 0

        payload = {
            "portfolio_value": round(self._portfolio_value, 2),
            "daily_pnl": round(self._daily_pnl, 2),
            "win_rate": round(win_rate, 1),
            "signal": signal,
            "sentiment": sentiment,
            "confidence": confidence,
            "trades": self._trades,
        }
        if PYQT6_AVAILABLE:
            self.tick.emit(payload)


# ---------------------------------------------------------------------------
# Reusable metric card widget
# ---------------------------------------------------------------------------

if PYQT6_AVAILABLE:
    class MetricCard(QFrame):
        """Small card displaying a labelled metric value."""

        def __init__(self, label: str, value: str = "—", parent=None) -> None:
            super().__init__(parent)
            self.setFrameShape(QFrame.Shape.StyledPanel)
            self.setStyleSheet(
                "QFrame { background-color: #0f3460; border-radius: 8px; border: 1px solid #2d2d44; }"
            )
            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(2)

            self._value_label = QLabel(value)
            self._value_label.setObjectName("metricValue")
            self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl = QLabel(label)
            lbl.setObjectName("metricLabel")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            layout.addWidget(self._value_label)
            layout.addWidget(lbl)

        def set_value(self, value: str, color: str = "#e94560") -> None:
            self._value_label.setText(value)
            self._value_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")


# ---------------------------------------------------------------------------
# Dashboard Tab
# ---------------------------------------------------------------------------

if PYQT6_AVAILABLE:
    class DashboardTab(QWidget):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self._build_ui()
            self._history: List[float] = []

        def _build_ui(self) -> None:
            main_layout = QVBoxLayout(self)
            main_layout.setSpacing(10)

            # ── Metric cards row ──────────────────────────────────────────
            cards_layout = QHBoxLayout()
            self.card_portfolio = MetricCard("Portfolio Value", "$10,000.00")
            self.card_pnl = MetricCard("Today's P&L", "$0.00")
            self.card_winrate = MetricCard("Win Rate", "0.0%")
            self.card_trades = MetricCard("Total Trades", "0")
            for card in (self.card_portfolio, self.card_pnl, self.card_winrate, self.card_trades):
                card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                cards_layout.addWidget(card)
            main_layout.addLayout(cards_layout)

            # ── Performance chart + activity log ─────────────────────────
            splitter = QSplitter(Qt.Orientation.Horizontal)

            # Chart
            chart_group = QGroupBox("📈  Portfolio Performance")
            chart_layout = QVBoxLayout(chart_group)
            if MATPLOTLIB_AVAILABLE:
                self._fig = Figure(figsize=(5, 3), facecolor="#0f3460")
                self._ax = self._fig.add_subplot(111)
                self._ax.set_facecolor("#0d2840")
                self._ax.tick_params(colors="#aaaaaa")
                for spine in self._ax.spines.values():
                    spine.set_edgecolor("#2d2d44")
                self._canvas = FigureCanvas(self._fig)
                self._canvas.setStyleSheet("background-color: #0f3460;")
                chart_layout.addWidget(self._canvas)
            else:
                chart_layout.addWidget(QLabel("Install matplotlib to see the chart."))

            # Activity log
            log_group = QGroupBox("📋  Live Activity Log")
            log_layout = QVBoxLayout(log_group)
            self.activity_log = QTextEdit()
            self.activity_log.setReadOnly(True)
            self.activity_log.setMaximumBlockCount(500)
            log_layout.addWidget(self.activity_log)

            splitter.addWidget(chart_group)
            splitter.addWidget(log_group)
            splitter.setSizes([500, 300])
            main_layout.addWidget(splitter)

            # ── Status row ───────────────────────────────────────────────
            status_layout = QHBoxLayout()
            self.lbl_engine_status = QLabel("⬤  Engine: IDLE")
            self.lbl_engine_status.setStyleSheet("color: #888888;")
            self.lbl_market_status = QLabel("⬤  Market: CLOSED")
            self.lbl_market_status.setStyleSheet("color: #888888;")
            self.lbl_paper_status = QLabel("📄  Paper Trading: ON")
            self.lbl_paper_status.setStyleSheet("color: #3399ff;")
            status_layout.addWidget(self.lbl_engine_status)
            status_layout.addWidget(self.lbl_market_status)
            status_layout.addWidget(self.lbl_paper_status)
            status_layout.addStretch()
            main_layout.addLayout(status_layout)

        # ------------------------------------------------------------------

        def update_tick(self, data: dict) -> None:
            pv = data["portfolio_value"]
            pnl = data["daily_pnl"]
            wr = data["win_rate"]
            trades = data["trades"]

            self.card_portfolio.set_value(f"${pv:,.2f}")
            pnl_color = "#27ae60" if pnl >= 0 else "#e74c3c"
            sign = "+" if pnl >= 0 else ""
            self.card_pnl.set_value(f"{sign}${pnl:,.2f}", pnl_color)
            wr_color = "#27ae60" if wr >= 50 else "#e74c3c"
            self.card_winrate.set_value(f"{wr:.1f}%", wr_color)
            self.card_trades.set_value(str(trades))

            self._history.append(pv)
            if len(self._history) > 120:
                self._history = self._history[-120:]
            self._draw_chart()

        def add_trade_log(self, trade: dict) -> None:
            ts = trade["time"]
            sym = trade["symbol"]
            side = trade["side"]
            qty = trade["qty"]
            price = trade["price"]
            paper = " [PAPER]" if trade.get("paper") else ""
            color = "#27ae60" if side == "BUY" else "#e74c3c"
            self.activity_log.append(
                f'<span style="color:#888888">{ts}</span>  '
                f'<span style="color:{color}; font-weight:bold">{side}</span>  '
                f'{sym}  qty={qty}  @${price:,.2f}'
                f'<span style="color:#3399ff">{paper}</span>'
            )

        def set_engine_active(self, active: bool) -> None:
            if active:
                self.lbl_engine_status.setText("⬤  Engine: RUNNING")
                self.lbl_engine_status.setStyleSheet("color: #27ae60;")
            else:
                self.lbl_engine_status.setText("⬤  Engine: IDLE")
                self.lbl_engine_status.setStyleSheet("color: #888888;")

        def set_paper_mode(self, paper: bool) -> None:
            if paper:
                self.lbl_paper_status.setText("📄  Paper Trading: ON")
                self.lbl_paper_status.setStyleSheet("color: #3399ff;")
            else:
                self.lbl_paper_status.setText("💰  Live Trading: ON")
                self.lbl_paper_status.setStyleSheet("color: #27ae60;")

        def _draw_chart(self) -> None:
            if not MATPLOTLIB_AVAILABLE:
                return
            self._ax.clear()
            self._ax.set_facecolor("#0d2840")
            self._ax.tick_params(colors="#aaaaaa")
            for spine in self._ax.spines.values():
                spine.set_edgecolor("#2d2d44")
            x = list(range(len(self._history)))
            y = self._history
            self._ax.plot(x, y, color="#e94560", linewidth=1.5)
            if len(y) > 1:
                self._ax.fill_between(x, y, min(y), alpha=0.15, color="#e94560")
            self._ax.set_xlabel("Ticks", color="#aaaaaa", fontsize=9)
            self._ax.set_ylabel("Portfolio ($)", color="#aaaaaa", fontsize=9)
            self._fig.tight_layout(pad=0.5)
            self._canvas.draw()


# ---------------------------------------------------------------------------
# Trading Tab
# ---------------------------------------------------------------------------

if PYQT6_AVAILABLE:
    class TradingTab(QWidget):
        start_trading = pyqtSignal()
        stop_trading = pyqtSignal()
        paper_toggled = pyqtSignal(bool)
        emergency_stop = pyqtSignal()

        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self._trading = False
            self._build_ui()

        def _build_ui(self) -> None:
            layout = QVBoxLayout(self)
            layout.setSpacing(12)

            # ── Trading controls ──────────────────────────────────────────
            ctrl_group = QGroupBox("🎮  Trading Controls")
            ctrl_layout = QGridLayout(ctrl_group)

            self.btn_start = QPushButton("▶  START TRADING")
            self.btn_start.setObjectName("startBtn")
            self.btn_start.setMinimumHeight(50)
            self.btn_start.clicked.connect(self._toggle_trading)

            self.btn_stop = QPushButton("⏹  STOP TRADING")
            self.btn_stop.setObjectName("stopBtn")
            self.btn_stop.setMinimumHeight(50)
            self.btn_stop.setEnabled(False)
            self.btn_stop.clicked.connect(self._toggle_trading)

            self.chk_paper = QCheckBox("📄  Paper Trading Mode")
            self.chk_paper.setChecked(config.paper_trading)
            self.chk_paper.stateChanged.connect(
                lambda s: self.paper_toggled.emit(s == Qt.CheckState.Checked.value)
            )

            self.btn_emergency = QPushButton("🚨  EMERGENCY STOP")
            self.btn_emergency.setObjectName("emergencyBtn")
            self.btn_emergency.clicked.connect(self._on_emergency)

            ctrl_layout.addWidget(self.btn_start, 0, 0)
            ctrl_layout.addWidget(self.btn_stop, 0, 1)
            ctrl_layout.addWidget(self.chk_paper, 1, 0)
            ctrl_layout.addWidget(self.btn_emergency, 1, 1)
            layout.addWidget(ctrl_group)

            # ── Manual trade execution ────────────────────────────────────
            manual_group = QGroupBox("✍  Manual Trade Execution")
            manual_layout = QFormLayout(manual_group)

            self.cmb_symbol = QComboBox()
            self.cmb_symbol.addItems(["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"])
            self.cmb_side = QComboBox()
            self.cmb_side.addItems(["BUY", "SELL"])
            self.spin_qty = QDoubleSpinBox()
            self.spin_qty.setRange(0.0001, 100)
            self.spin_qty.setDecimals(4)
            self.spin_qty.setValue(0.001)
            self.btn_execute = QPushButton("Execute Trade")
            self.btn_execute.clicked.connect(self._execute_manual_trade)

            manual_layout.addRow("Symbol:", self.cmb_symbol)
            manual_layout.addRow("Side:", self.cmb_side)
            manual_layout.addRow("Quantity:", self.spin_qty)
            manual_layout.addRow("", self.btn_execute)
            layout.addWidget(manual_group)

            # ── Open positions ────────────────────────────────────────────
            pos_group = QGroupBox("📊  Open Positions")
            pos_layout = QVBoxLayout(pos_group)
            self.positions_table = QTableWidget(0, 6)
            self.positions_table.setHorizontalHeaderLabels(
                ["Symbol", "Side", "Qty", "Entry Price", "Current P&L", "Action"]
            )
            self.positions_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )
            pos_layout.addWidget(self.positions_table)
            layout.addWidget(pos_group)
            layout.addStretch()

        def _toggle_trading(self) -> None:
            self._trading = not self._trading
            self.btn_start.setEnabled(not self._trading)
            self.btn_stop.setEnabled(self._trading)
            if self._trading:
                self.start_trading.emit()
            else:
                self.stop_trading.emit()

        def _on_emergency(self) -> None:
            reply = QMessageBox.question(
                self,
                "Emergency Stop",
                "Close ALL positions and stop trading immediately?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._trading = False
                self.btn_start.setEnabled(True)
                self.btn_stop.setEnabled(False)
                self.positions_table.setRowCount(0)
                self.emergency_stop.emit()

        def _execute_manual_trade(self) -> None:
            symbol = self.cmb_symbol.currentText()
            side = self.cmb_side.currentText()
            qty = self.spin_qty.value()
            paper_tag = " [PAPER]" if self.chk_paper.isChecked() else ""
            QMessageBox.information(
                self,
                "Trade Submitted",
                f"{side} {qty} {symbol}{paper_tag} submitted successfully.",
            )

        def set_trading_state(self, active: bool) -> None:
            self._trading = active
            self.btn_start.setEnabled(not active)
            self.btn_stop.setEnabled(active)


# ---------------------------------------------------------------------------
# Analysis Tab
# ---------------------------------------------------------------------------

if PYQT6_AVAILABLE:
    class AnalysisTab(QWidget):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self._build_ui()

        def _build_ui(self) -> None:
            layout = QVBoxLayout(self)
            layout.setSpacing(10)

            # ── AI signals ───────────────────────────────────────────────
            signals_group = QGroupBox("🤖  AI Signal Indicators")
            sig_layout = QGridLayout(signals_group)

            headers = ["Asset", "Sentiment", "Signal", "Confidence", "Risk Level"]
            for col, h in enumerate(headers):
                lbl = QLabel(h)
                lbl.setStyleSheet("font-weight: bold; color: #aab7d4;")
                sig_layout.addWidget(lbl, 0, col)

            self._signal_rows = []
            assets = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
            for row, asset in enumerate(assets, start=1):
                asset_lbl = QLabel(asset)
                sent_bar = QProgressBar()
                sent_bar.setRange(-100, 100)
                sent_bar.setValue(0)
                sent_bar.setFormat("%v%")
                signal_lbl = QLabel("HOLD")
                signal_lbl.setObjectName("signalNeutral")
                conf_lbl = QLabel("—")
                risk_lbl = QLabel("LOW")
                risk_lbl.setStyleSheet("color: #27ae60;")
                sig_layout.addWidget(asset_lbl, row, 0)
                sig_layout.addWidget(sent_bar, row, 1)
                sig_layout.addWidget(signal_lbl, row, 2)
                sig_layout.addWidget(conf_lbl, row, 3)
                sig_layout.addWidget(risk_lbl, row, 4)
                self._signal_rows.append((sent_bar, signal_lbl, conf_lbl, risk_lbl))
            layout.addWidget(signals_group)

            # ── Risk warnings ────────────────────────────────────────────
            risk_group = QGroupBox("⚠️  Risk Warnings")
            risk_layout = QVBoxLayout(risk_group)
            self.risk_log = QTextEdit()
            self.risk_log.setReadOnly(True)
            self.risk_log.setMaximumHeight(120)
            risk_layout.addWidget(self.risk_log)
            layout.addWidget(risk_group)

            # ── News sentiment feed ───────────────────────────────────────
            news_group = QGroupBox("📰  News Sentiment Feed")
            news_layout = QVBoxLayout(news_group)
            self.news_log = QTextEdit()
            self.news_log.setReadOnly(True)
            news_layout.addWidget(self.news_log)
            layout.addWidget(news_group)

        def update_tick(self, data: dict) -> None:
            sent = data.get("sentiment", 0)
            signal = data.get("signal", "HOLD")
            conf = data.get("confidence", 0)
            idx = hash(data.get("signal", "")) % len(self._signal_rows)
            row = self._signal_rows[idx]
            sent_bar, signal_lbl, conf_lbl, risk_lbl = row
            sent_bar.setValue(int(sent * 100))
            signal_lbl.setText(signal)
            if signal == "BUY":
                signal_lbl.setObjectName("signalBull")
            elif signal == "SELL":
                signal_lbl.setObjectName("signalBear")
            else:
                signal_lbl.setObjectName("signalNeutral")
            signal_lbl.setStyleSheet("")  # force re-apply
            conf_lbl.setText(f"{conf:.0%}")
            risk = "HIGH" if abs(sent) > 0.7 else ("MEDIUM" if abs(sent) > 0.3 else "LOW")
            risk_colors = {"HIGH": "#e74c3c", "MEDIUM": "#f39c12", "LOW": "#27ae60"}
            risk_lbl.setText(risk)
            risk_lbl.setStyleSheet(f"color: {risk_colors[risk]};")

        def add_news(self, text: str) -> None:
            self.news_log.append(text)

        def add_risk_warning(self, text: str) -> None:
            self.risk_log.append(
                f'<span style="color:#f39c12">⚠ {text}</span>'
            )


# ---------------------------------------------------------------------------
# Settings Tab
# ---------------------------------------------------------------------------

if PYQT6_AVAILABLE:
    class SettingsTab(QWidget):
        settings_saved = pyqtSignal()

        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self._build_ui()
            self._load_from_config()

        def _build_ui(self) -> None:
            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            outer = QVBoxLayout(self)
            outer.addWidget(scroll)

            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setSpacing(12)
            scroll.setWidget(container)

            # ── API Keys ──────────────────────────────────────────────────
            api_group = QGroupBox("🔑  API Key Management")
            api_form = QFormLayout(api_group)
            self.txt_exchange_key = QLineEdit()
            self.txt_exchange_key.setEchoMode(QLineEdit.EchoMode.Password)
            self.txt_exchange_secret = QLineEdit()
            self.txt_exchange_secret.setEchoMode(QLineEdit.EchoMode.Password)
            self.txt_news_api = QLineEdit()
            self.txt_news_api.setEchoMode(QLineEdit.EchoMode.Password)
            self.txt_openai_key = QLineEdit()
            self.txt_openai_key.setEchoMode(QLineEdit.EchoMode.Password)
            api_form.addRow("Exchange API Key:", self.txt_exchange_key)
            api_form.addRow("Exchange Secret:", self.txt_exchange_secret)
            api_form.addRow("News API Key:", self.txt_news_api)
            api_form.addRow("OpenAI API Key:", self.txt_openai_key)
            layout.addWidget(api_group)

            # ── Exchange ──────────────────────────────────────────────────
            exc_group = QGroupBox("🏦  Exchange & Market")
            exc_form = QFormLayout(exc_group)
            self.cmb_exchange = QComboBox()
            self.cmb_exchange.addItems(["binance", "coinbase", "kraken", "bybit", "okx"])
            self.txt_symbols = QLineEdit()
            self.txt_symbols.setPlaceholderText("BTC/USDT, ETH/USDT")
            exc_form.addRow("Exchange:", self.cmb_exchange)
            exc_form.addRow("Symbols (comma-separated):", self.txt_symbols)
            layout.addWidget(exc_group)

            # ── Trading parameters ────────────────────────────────────────
            trade_group = QGroupBox("📈  Trading Parameters")
            trade_form = QFormLayout(trade_group)

            self.spin_max_pos = QDoubleSpinBox()
            self.spin_max_pos.setRange(0.001, 1.0)
            self.spin_max_pos.setSingleStep(0.01)
            self.spin_max_pos.setDecimals(3)
            self.spin_max_pos.setSuffix("  (fraction)")

            self.spin_risk = QDoubleSpinBox()
            self.spin_risk.setRange(0.001, 0.5)
            self.spin_risk.setSingleStep(0.005)
            self.spin_risk.setDecimals(3)
            self.spin_risk.setSuffix("  (fraction)")

            self.spin_sl = QDoubleSpinBox()
            self.spin_sl.setRange(0.001, 0.5)
            self.spin_sl.setSingleStep(0.005)
            self.spin_sl.setDecimals(3)
            self.spin_sl.setSuffix("  (fraction)")

            self.spin_tp = QDoubleSpinBox()
            self.spin_tp.setRange(0.001, 1.0)
            self.spin_tp.setSingleStep(0.01)
            self.spin_tp.setDecimals(3)
            self.spin_tp.setSuffix("  (fraction)")

            self.spin_max_open = QSpinBox()
            self.spin_max_open.setRange(1, 20)

            trade_form.addRow("Max Position Size:", self.spin_max_pos)
            trade_form.addRow("Risk Per Trade:", self.spin_risk)
            trade_form.addRow("Stop Loss %:", self.spin_sl)
            trade_form.addRow("Take Profit %:", self.spin_tp)
            trade_form.addRow("Max Open Positions:", self.spin_max_open)
            layout.addWidget(trade_group)

            # ── AI Model ──────────────────────────────────────────────────
            model_group = QGroupBox("🧠  AI Model Selection")
            model_form = QFormLayout(model_group)

            self.cmb_sentiment = QComboBox()
            self.cmb_sentiment.addItems(["finbert", "fingpt", "vader", "textblob"])
            self.cmb_decision = QComboBox()
            self.cmb_decision.addItems(["ensemble", "lstm", "gru", "llm"])
            self.cmb_ollama = QComboBox()
            self.cmb_ollama.addItems(["llama3", "mistral", "gemma", "codellama"])
            self.cmb_ollama.setEditable(True)

            model_form.addRow("Sentiment Model:", self.cmb_sentiment)
            model_form.addRow("Decision Model:", self.cmb_decision)
            model_form.addRow("Ollama Model:", self.cmb_ollama)
            layout.addWidget(model_group)

            # ── Application ───────────────────────────────────────────────
            app_group = QGroupBox("⚙️  Application Settings")
            app_form = QFormLayout(app_group)
            self.chk_startup = QCheckBox("Start with Windows")
            self.chk_tray = QCheckBox("Minimize to system tray")
            self.chk_dark = QCheckBox("Dark mode")
            self.chk_autoconnect = QCheckBox("Auto-connect to exchange on startup")
            app_form.addRow(self.chk_startup)
            app_form.addRow(self.chk_tray)
            app_form.addRow(self.chk_dark)
            app_form.addRow(self.chk_autoconnect)
            layout.addWidget(app_group)

            # ── Save / Reset ──────────────────────────────────────────────
            btn_layout = QHBoxLayout()
            btn_save = QPushButton("💾  Save Settings")
            btn_save.clicked.connect(self._save_settings)
            btn_reset = QPushButton("↩  Reset Defaults")
            btn_reset.clicked.connect(self._reset_defaults)
            btn_layout.addStretch()
            btn_layout.addWidget(btn_reset)
            btn_layout.addWidget(btn_save)
            layout.addLayout(btn_layout)
            layout.addStretch()

        def _load_from_config(self) -> None:
            keys = config.get_section("api_keys")
            self.txt_exchange_key.setText(keys.get("exchange_api_key", ""))
            self.txt_exchange_secret.setText(keys.get("exchange_api_secret", ""))
            self.txt_news_api.setText(keys.get("news_api_key", ""))
            self.txt_openai_key.setText(keys.get("openai_api_key", ""))

            exc = config.get_section("exchange")
            idx = self.cmb_exchange.findText(exc.get("name", "binance"))
            if idx >= 0:
                self.cmb_exchange.setCurrentIndex(idx)
            self.txt_symbols.setText(", ".join(exc.get("symbols", [])))

            tr = config.get_section("trading")
            self.spin_max_pos.setValue(tr.get("max_position_size", 0.05))
            self.spin_risk.setValue(tr.get("risk_per_trade", 0.01))
            self.spin_sl.setValue(tr.get("stop_loss_pct", 0.02))
            self.spin_tp.setValue(tr.get("take_profit_pct", 0.06))
            self.spin_max_open.setValue(tr.get("max_open_positions", 5))

            mdl = config.get_section("model")
            self.cmb_sentiment.setCurrentText(mdl.get("sentiment_model", "finbert"))
            self.cmb_decision.setCurrentText(mdl.get("decision_model", "ensemble"))
            self.cmb_ollama.setCurrentText(mdl.get("ollama_model", "llama3"))

            app = config.get_section("app")
            self.chk_startup.setChecked(app.get("start_with_windows", False))
            self.chk_tray.setChecked(app.get("minimize_to_tray", True))
            self.chk_dark.setChecked(app.get("dark_mode", True))
            self.chk_autoconnect.setChecked(app.get("auto_connect", False))

        def _save_settings(self) -> None:
            config.set_section("api_keys", {
                "exchange_api_key": self.txt_exchange_key.text(),
                "exchange_api_secret": self.txt_exchange_secret.text(),
                "news_api_key": self.txt_news_api.text(),
                "openai_api_key": self.txt_openai_key.text(),
            })
            symbols = [s.strip() for s in self.txt_symbols.text().split(",") if s.strip()]
            config.set_section("exchange", {
                "name": self.cmb_exchange.currentText(),
                "symbols": symbols,
                "base_currency": "USDT",
            })
            config.set_section("trading", {
                "paper_trading": config.paper_trading,
                "max_position_size": self.spin_max_pos.value(),
                "risk_per_trade": self.spin_risk.value(),
                "stop_loss_pct": self.spin_sl.value(),
                "take_profit_pct": self.spin_tp.value(),
                "max_open_positions": self.spin_max_open.value(),
                "trade_cooldown_seconds": 60,
            })
            config.set_section("model", {
                "sentiment_model": self.cmb_sentiment.currentText(),
                "decision_model": self.cmb_decision.currentText(),
                "ollama_model": self.cmb_ollama.currentText(),
            })
            startup = self.chk_startup.isChecked()
            config.set_section("app", {
                "start_with_windows": startup,
                "minimize_to_tray": self.chk_tray.isChecked(),
                "dark_mode": self.chk_dark.isChecked(),
                "auto_connect": self.chk_autoconnect.isChecked(),
                "log_level": "INFO",
                "theme": "dark" if self.chk_dark.isChecked() else "light",
            })
            config.apply_startup_setting(startup)
            config.save()
            self.settings_saved.emit()
            QMessageBox.information(self, "Settings", "Settings saved successfully.")

        def _reset_defaults(self) -> None:
            reply = QMessageBox.question(
                self,
                "Reset Settings",
                "Reset all settings to defaults?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Yes:
                config.reset_to_defaults()
                self._load_from_config()


# ---------------------------------------------------------------------------
# System Status Tab
# ---------------------------------------------------------------------------

if PYQT6_AVAILABLE:
    class StatusTab(QWidget):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self._build_ui()

        def _build_ui(self) -> None:
            layout = QVBoxLayout(self)
            layout.setSpacing(10)

            # ── Resource usage ────────────────────────────────────────────
            res_group = QGroupBox("💻  System Resources")
            res_layout = QFormLayout(res_group)

            self.bar_cpu = QProgressBar()
            self.bar_cpu.setRange(0, 100)
            self.bar_cpu.setFormat("%v%")
            self.bar_ram = QProgressBar()
            self.bar_ram.setRange(0, 100)
            self.bar_ram.setFormat("%v%")
            self.bar_gpu = QProgressBar()
            self.bar_gpu.setRange(0, 100)
            self.bar_gpu.setFormat("%v%")
            self.lbl_gpu_info = QLabel("GPU: Not detected")

            res_layout.addRow("CPU Usage:", self.bar_cpu)
            res_layout.addRow("RAM Usage:", self.bar_ram)
            res_layout.addRow("GPU Usage:", self.bar_gpu)
            res_layout.addRow("", self.lbl_gpu_info)
            layout.addWidget(res_group)

            # ── Connection status ─────────────────────────────────────────
            conn_group = QGroupBox("🌐  Connection Status")
            conn_layout = QFormLayout(conn_group)

            self.lbl_exchange = QLabel("● Disconnected")
            self.lbl_exchange.setStyleSheet("color: #e74c3c;")
            self.lbl_news = QLabel("● Disconnected")
            self.lbl_news.setStyleSheet("color: #e74c3c;")
            self.lbl_ai = QLabel("● Disconnected")
            self.lbl_ai.setStyleSheet("color: #e74c3c;")

            conn_layout.addRow("Exchange:", self.lbl_exchange)
            conn_layout.addRow("News Feed:", self.lbl_news)
            conn_layout.addRow("AI Service:", self.lbl_ai)
            layout.addWidget(conn_group)

            # ── Application log ───────────────────────────────────────────
            log_group = QGroupBox("📄  Application Log")
            log_layout = QVBoxLayout(log_group)
            self.app_log = QTextEdit()
            self.app_log.setReadOnly(True)
            self.app_log.setFont(QFont("Consolas", 10))
            self.app_log.setMaximumBlockCount(1000)
            log_layout.addWidget(self.app_log)
            layout.addWidget(log_group)

        def update_resources(self) -> None:
            if PSUTIL_AVAILABLE:
                cpu = int(psutil.cpu_percent(interval=None))
                ram = int(psutil.virtual_memory().percent)
            else:
                cpu = random.randint(5, 40)
                ram = random.randint(30, 70)
            self.bar_cpu.setValue(cpu)
            self.bar_ram.setValue(ram)
            # GPU usage placeholder
            self.bar_gpu.setValue(0)

        def set_connected(self, service: str, connected: bool) -> None:
            label_map = {
                "exchange": self.lbl_exchange,
                "news": self.lbl_news,
                "ai": self.lbl_ai,
            }
            lbl = label_map.get(service)
            if lbl:
                if connected:
                    lbl.setText("● Connected")
                    lbl.setStyleSheet("color: #27ae60;")
                else:
                    lbl.setText("● Disconnected")
                    lbl.setStyleSheet("color: #e74c3c;")

        def append_log(self, message: str) -> None:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.app_log.append(f"[{ts}]  {message}")


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

if PYQT6_AVAILABLE:
    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("AI Trading System")
            self.setMinimumSize(1100, 700)
            self.resize(1280, 800)

            self._trading_active = False
            self._paper_mode = config.paper_trading

            self._apply_theme()
            self._build_ui()
            self._setup_tray()
            self._setup_engine()
            self._setup_timers()

            self.status_tab.append_log("Application started.")

        # ------------------------------------------------------------------
        # UI construction
        # ------------------------------------------------------------------

        def _apply_theme(self) -> None:
            sheet = DARK_STYLESHEET if config.dark_mode else LIGHT_STYLESHEET
            self.setStyleSheet(sheet)

        def _build_ui(self) -> None:
            central = QWidget()
            self.setCentralWidget(central)
            root = QVBoxLayout(central)
            root.setContentsMargins(6, 6, 6, 6)

            # Header
            header = QLabel("🤖  AI TRADING SYSTEM")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #e94560; padding: 6px;"
            )
            root.addWidget(header)

            # Tabs
            self.tabs = QTabWidget()
            self.dashboard_tab = DashboardTab()
            self.trading_tab = TradingTab()
            self.analysis_tab = AnalysisTab()
            self.settings_tab = SettingsTab()
            self.status_tab = StatusTab()

            self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")
            self.tabs.addTab(self.trading_tab, "🎮 Trading")
            self.tabs.addTab(self.analysis_tab, "🔍 Analysis")
            self.tabs.addTab(self.settings_tab, "⚙️ Settings")
            self.tabs.addTab(self.status_tab, "🖥 Status")
            root.addWidget(self.tabs)

            # Status bar
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("Ready  |  Paper Trading Mode")

            # Connect trading tab signals
            self.trading_tab.start_trading.connect(self._on_start_trading)
            self.trading_tab.stop_trading.connect(self._on_stop_trading)
            self.trading_tab.paper_toggled.connect(self._on_paper_toggled)
            self.trading_tab.emergency_stop.connect(self._on_emergency_stop)
            self.settings_tab.settings_saved.connect(self._on_settings_saved)

        def _setup_tray(self) -> None:
            self.tray = SystemTrayManager(self)
            self.tray.show_window_requested.connect(self._show_from_tray)
            self.tray.quit_requested.connect(self._quit_app)
            self.tray.toggle_trading_requested.connect(self._tray_toggle_trading)
            self.tray.set_paper_trading(self._paper_mode)

        def _setup_engine(self) -> None:
            self._engine = TradingEngine()
            self._engine_thread = QThread()
            self._engine.moveToThread(self._engine_thread)
            self._engine_thread.started.connect(self._engine.run)
            self._engine.tick.connect(self._on_engine_tick)
            self._engine.trade_executed.connect(self._on_trade_executed)

        def _setup_timers(self) -> None:
            # Resource monitor
            self._res_timer = QTimer(self)
            self._res_timer.timeout.connect(self.status_tab.update_resources)
            self._res_timer.start(3000)

            # Demo news feed
            self._news_timer = QTimer(self)
            self._news_timer.timeout.connect(self._push_demo_news)
            self._news_timer.start(15_000)

        # ------------------------------------------------------------------
        # Slots
        # ------------------------------------------------------------------

        def _on_start_trading(self) -> None:
            self._trading_active = True
            self._engine.set_paper(self._paper_mode)
            if not self._engine_thread.isRunning():
                self._engine_thread.start()
            self.dashboard_tab.set_engine_active(True)
            self.tray.set_trading_active(True)
            mode = "Paper" if self._paper_mode else "Live"
            self.status_bar.showMessage(f"Trading ACTIVE  |  {mode} Mode")
            self.tray.show_message("AI Trading", f"{mode} trading started.")
            self.status_tab.append_log(f"Trading started ({mode} mode).")
            logger.info("Trading started.")

        def _on_stop_trading(self) -> None:
            self._trading_active = False
            self._engine.stop()
            self.dashboard_tab.set_engine_active(False)
            self.tray.set_trading_active(False)
            self.status_bar.showMessage("Trading STOPPED  |  Paper Trading Mode")
            self.tray.show_message("AI Trading", "Trading stopped.")
            self.status_tab.append_log("Trading stopped.")
            logger.info("Trading stopped.")

        def _on_paper_toggled(self, paper: bool) -> None:
            self._paper_mode = paper
            config.paper_trading = paper
            config.save()
            self.dashboard_tab.set_paper_mode(paper)
            self.tray.set_paper_trading(paper)
            mode = "Paper" if paper else "Live"
            self.status_bar.showMessage(
                f"{'Trading ACTIVE' if self._trading_active else 'Ready'}  |  {mode} Mode"
            )
            self.status_tab.append_log(f"Switched to {mode} trading mode.")

        def _on_emergency_stop(self) -> None:
            self._trading_active = False
            self._engine.stop()
            self.dashboard_tab.set_engine_active(False)
            self.tray.set_state("error", "AI Trading – EMERGENCY STOP")
            self.status_bar.showMessage("🚨 EMERGENCY STOP TRIGGERED")
            self.tray.show_message(
                "Emergency Stop",
                "All positions closed and trading halted.",
                duration_ms=8000,
            )
            self.analysis_tab.add_risk_warning("EMERGENCY STOP triggered by user.")
            self.status_tab.append_log("EMERGENCY STOP triggered.")
            logger.warning("Emergency stop triggered.")

        def _on_engine_tick(self, data: dict) -> None:
            self.dashboard_tab.update_tick(data)
            self.analysis_tab.update_tick(data)

        def _on_trade_executed(self, trade: dict) -> None:
            self.dashboard_tab.add_trade_log(trade)
            self.status_tab.append_log(
                f"Trade: {trade['side']} {trade['qty']} {trade['symbol']} @ ${trade['price']:,.2f}"
            )

        def _on_settings_saved(self) -> None:
            self._apply_theme()
            self.status_tab.append_log("Settings saved.")

        def _show_from_tray(self) -> None:
            self.showNormal()
            self.activateWindow()

        def _quit_app(self) -> None:
            self._engine.stop()
            if self._engine_thread.isRunning():
                self._engine_thread.quit()
                self._engine_thread.wait(2000)
            self.tray.hide()
            QApplication.quit()

        def _tray_toggle_trading(self) -> None:
            if self._trading_active:
                self._on_stop_trading()
                self.trading_tab.set_trading_state(False)
            else:
                self._on_start_trading()
                self.trading_tab.set_trading_state(True)

        def _push_demo_news(self) -> None:
            headlines = [
                "Bitcoin surges past key resistance level amid ETF inflows.",
                "Fed signals potential rate cuts – risk assets rally.",
                "Ethereum network upgrade improves throughput by 30%.",
                "Crypto market cap hits $2T milestone for first time in months.",
                "DeFi protocol exploited for $12M – market reacts cautiously.",
                "Institutional adoption of crypto accelerates in Q1.",
            ]
            sentiment_labels = ["POSITIVE 📈", "NEGATIVE 📉", "NEUTRAL ➡️"]
            headline = random.choice(headlines)
            sent = random.choice(sentiment_labels)
            ts = datetime.datetime.now().strftime("%H:%M")
            self.analysis_tab.add_news(
                f'<span style="color:#888888">[{ts}]</span>  '
                f'<span style="color:#e0e0e0">{headline}</span>  '
                f'<span style="color:#f39c12">{sent}</span>'
            )

        # ------------------------------------------------------------------
        # Window events
        # ------------------------------------------------------------------

        def closeEvent(self, event) -> None:
            if config.minimize_to_tray:
                event.ignore()
                self.hide()
                self.tray.show_message(
                    "AI Trading",
                    "Application minimized to tray. Double-click the icon to restore.",
                )
            else:
                self._quit_app()
                event.accept()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
    )

    if not PYQT6_AVAILABLE:
        logger.error(
            "PyQt6 is required to run the GUI. Install it with: pip install PyQt6"
        )
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("AI Trading System")
    app.setOrganizationName("AITrading")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
