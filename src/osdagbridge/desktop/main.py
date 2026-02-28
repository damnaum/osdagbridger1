"""Desktop GUI bootstrap (PySide6).

Requires the 'desktop' extra: pip install -e ".[desktop]"
"""
import sys


def start():
    """Launch the desktop application."""
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: F401

        _app = QApplication(sys.argv)
        msg = QMessageBox()
        msg.setWindowTitle("OsdagBridge")
        msg.setText("Desktop interface is under development.\nUse the CLI for now.")
        msg.exec()
    except ImportError:
        print(
            "PySide6 is not installed.\n"
            "Install with: pip install -e '.[desktop]'\n"
            "Alternatively, use the CLI: osdagbridge analyze <input.yaml>"
        )
        sys.exit(1)


if __name__ == "__main__":
    start()

