import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setGeometry(1000, 795, 70, 70)
    

class MyLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.setStyleSheet("font-size: 48px; color: red;")
        pixmap = QtGui.QPixmap("./assets/idle.png")
        self.setPixmap(pixmap)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    widget = MyWidget()      
    widget.show()
    label = MyLabel(widget)
    label.setGeometry(widget.rect())
    label.show()
    sys.exit(app.exec())