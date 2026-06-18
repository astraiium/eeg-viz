import sys
from PyQt6.QtWidgets import QApplication

from config import load_config
from gui import MainWindow

config = load_config()

app = QApplication(sys.argv)

window = MainWindow(config)
window.show()

sys.exit(app.exec())
