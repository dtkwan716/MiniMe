import sys
import random
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QPropertyAnimation

QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.screen = QtWidgets.QApplication.primaryScreen()
        self.available_geometry = self.screen.availableGeometry()
        self.is_walking = False

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.starting_x = self.available_geometry.x() + self.available_geometry.width() - 84
        self.starting_y = self.available_geometry.y() + self.available_geometry.height() - 64
        self.setGeometry(self.starting_x, self.starting_y, 64, 64)


        self.event_timer = QtCore.QTimer(self)
        self.event_timer.timeout.connect(self.decide_event)
        self.event_timer.start(200)

        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.setInterval(300)

    def decide_event(self):
        if self.is_walking:
            return

        if random.randint(0, 1) == 0:
            self.walk()


    def walk(self):
        self.is_walking = True
        self.event_timer.stop()
        self.animation_timer.start()

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setStartValue(self.pos())
        destination = random.randint(self.available_geometry.x(), self.available_geometry.x() + self.available_geometry.width() - self.width())
        self.anim.setEndValue(QtCore.QPoint(destination, self.pos().y()))
        distance = destination - self.pos().x()
        self.anim.setDuration(max(1, int(abs(distance / 0.1))))
        self.label.face_right = distance > 0
        self.anim.start()
        self.anim.finished.connect(self.done_walking)

    def done_walking(self):
        self.is_walking = False
        self.animation_timer.stop()
        self.label.setPixmap(self.label.walking_animation[0])
        self.event_timer.start(random.randint(1000, 5000))

class MySprite(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "Walk.png")
        )

        frame_size = sprite_sheet.width() // 3
        frame_positions = [(column, row) for row in range(3) for column in range(3)]
        frame_positions = frame_positions[:7]
        self.walking_animation = [
            sprite_sheet.copy(column * frame_size, row * frame_size, frame_size, frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in frame_positions
        ]       

        self.walk_current_frame = 0
        self.walk_loop_frame = 2

        self.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.setPixmap(self.walking_animation[self.walk_current_frame])

    def walk_next_frame(self):
        if self.walk_current_frame < len(self.walking_animation) - 1:
            self.walk_current_frame += 1
        else:
            self.walk_current_frame = self.walk_loop_frame

        frame = self.walking_animation[self.walk_current_frame]

        if self.face_right:
            frame = frame.transformed(QtGui.QTransform().scale(-1, 1))
        self.setPixmap(frame)
        self.resize(self.pixmap().size())

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()
    label = MySprite(widget)
    widget.label = label
    widget.animation_timer.timeout.connect(label.walk_next_frame)
    widget.show()
    label.resize(label.pixmap().size())    
    label.show()
    sys.exit(app.exec())


