import os, sys
sys.path.insert(0, "/tmp/m"); from mem import report
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import QTimer
app = QApplication(sys.argv); w = QLabel("hola"); w.resize(300, 40); w.show()
hold = int(os.environ.get("HOLD", "0"))
def done():
    report(os.environ.get("TAG", "qt6-pyside6"))
    QTimer.singleShot(hold * 1000 if hold else 0, app.quit)
QTimer.singleShot(6000, done); app.exec()
