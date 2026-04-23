import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.MainWindow import MainWindow
from dotenv import load_dotenv
from pathlib import Path

def main():
    # Load .env if exists
    load_dotenv()

    app = QApplication(sys.argv)
    app.setApplicationName("PageIndex PyQt5")

    # Ensure current directory is in sys.path for core imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    window = MainWindow(current_dir)
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
