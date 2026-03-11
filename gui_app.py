import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel

class TradingSystemGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Trading System')
        self.setGeometry(100, 100, 800, 600)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel('Welcome to the Trading System')
        layout.addWidget(self.label)

        self.start_button = QPushButton('Start Trading')
        self.start_button.clicked.connect(self.start_trading)
        layout.addWidget(self.start_button)

        self.quit_button = QPushButton('Quit')
        self.quit_button.clicked.connect(self.close)
        layout.addWidget(self.quit_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_trading(self):
        # Trading logic goes here
        self.label.setText('Trading has started!')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TradingSystemGUI()
    window.show()
    sys.exit(app.exec())