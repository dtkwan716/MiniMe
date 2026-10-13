from ast import walk
import sys
import random
import ctypes
from ctypes import wintypes
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QPropertyAnimation
from sprite_loader import load_file


QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.screen = QtWidgets.QApplication.primaryScreen()
        self.available_geometry = self.screen.availableGeometry()
        self.in_animation = False

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.starting_x = self.available_geometry.x() + self.available_geometry.width() - 75
        self.starting_y = self.available_geometry.y() + self.available_geometry.height() - 64
        self.setGeometry(self.starting_x, self.starting_y, 64, 64)
        


        self.event_timer = QtCore.QTimer(self)
        self.event_timer.timeout.connect(self.decide_event)
        self.event_timer.start(200)

        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.setInterval(200)

        self.check_idle_timer = QtCore.QTimer(self)
        self.check_idle_timer.setInterval(1000)
        self.check_idle_timer.timeout.connect(self.check_idle)
        self.check_idle_timer.start()

        self.dragging = False
        self.mousePressed = False
        self.drag_position = None
        self.is_sleeping = False
        self.going_to_sleep = False
        self.balloonFall = False
        self.falling = False
        self.work_mode = False

        self.stopwatch = QtCore.QElapsedTimer()
        self.stopwatch_timer = QtCore.QTimer(self)
        self.stopwatch_timer.setInterval(100)
        self.stopwatch_timer.timeout.connect(self.update_stopwatch)
        self.stopwatch_label = QtWidgets.QLabel("00:00:00", self)
        self.stopwatch_label.setAlignment(QtCore.Qt.AlignCenter)
        self.stopwatch_label.setStyleSheet("color: dark green; font-size: 16px; background: beige; border-radius: 8px;")
        self.stopwatch_label.hide()
    
    def update_stopwatch(self):
        total_seconds = self.stopwatch.elapsed() // 1000
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.stopwatch_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")

    def working(self, event):
        if self.work_mode:
            self.work_mode = False
            self.stopwatch_label.hide()
            self.stopwatch_timer.stop()
            self.done_work()

        else:
            self.work_mode = True
            self.event_timer.stop()
            self.done_animation()
            self.in_animation = True
            self.going_to_sleep = True
            self.animation_timer.stop()
            if hasattr(self, 'anim') and not self.balloonFall:
                self.anim.stop()
            for timer_name in ("heart_timer", "wave_timer", "eat_timer", "hit_timer", "wakeup_timer", "toSleep_timer"):
                if hasattr(self, timer_name):
                    getattr(self, timer_name).stop()
            self.label.current_animation = self.label.walking_animation
            self.label.current_frame = 0
            self.label.loop_frame = 3
            self.animation_timer.setInterval(200)
            self.animation_timer.start()
            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setStartValue(self.pos())
            self.anim.setEndValue(QtCore.QPoint(self.starting_x, self.pos().y()))
            distance = self.starting_x - self.pos().x()
            self.anim.setDuration(max(1, int(abs(distance / 0.06))))
            self.label.face_right = distance > 0
            self.anim.start()
            self.stopwatch.restart()
            self.anim.finished.connect(self.work)

        

    def decide_event(self):
        if self.in_animation:
            return

        event = {
            'walk': self.walk,
            'heart': self.heart,
            'wave': self.wave,
            'eat': self.eat,
        }

        event = random.choice(list(event.values()))
        event()

    def get_idle_time(self):
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.UINT),
                ("dwTime", wintypes.DWORD),
            ]

        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(info)
        success = ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
        if not success:
            return
        last_input_tick = info.dwTime
        current_tick = ctypes.windll.kernel32.GetTickCount()
        self.idle_time = (current_tick - last_input_tick) & 0xFFFFFFFF
        return self.idle_time

    def check_idle(self):
        self.get_idle_time()
        if self.idle_time is None:
            return
        elif self.dragging or self.mousePressed or self.work_mode:
            return
        elif self.idle_time > 60000 and not self.is_sleeping and not self.going_to_sleep:
            self.event_timer.stop()
            self.in_animation = True
            self.going_to_sleep = True
            self.animation_timer.stop()
            if hasattr(self, 'anim') and not self.balloonFall:
                self.anim.stop()
            for timer_name in ("heart_timer", "wave_timer", "eat_timer", "hit_timer", "wakeup_timer"):
                if hasattr(self, timer_name):
                    getattr(self, timer_name).stop()
            self.label.current_animation = self.label.walking_animation
            self.label.current_frame = 0
            self.label.loop_frame = 3
            self.animation_timer.start()
            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setStartValue(self.pos())
            self.anim.setEndValue(QtCore.QPoint(self.starting_x, self.pos().y()))
            distance = self.starting_x - self.pos().x()
            self.anim.setDuration(max(1, int(abs(distance / 0.06))))
            self.label.face_right = distance > 0
            self.anim.start()
            self.anim.finished.connect(self.toSleep)
        elif self.idle_time < 1000 and (self.is_sleeping or self.going_to_sleep):
            if hasattr(self, "toSleep_timer"):
                self.toSleep_timer.stop()
            self.going_to_sleep = False
            self.event_timer.stop()
            self.in_animation = True
            self.animation_timer.stop()
            if hasattr(self, 'anim') and not self.balloonFall:
                self.anim.stop()
            for timer_name in ("heart_timer", "wave_timer", "eat_timer", "hit_timer", "wakeup_timer"):
                if hasattr(self, timer_name):
                    getattr(self, timer_name).stop()
            if self.is_sleeping:
                self.wakeup()
            else:
                self.done_animation()

    def walk(self):
        self.in_animation = True
        self.event_timer.stop()
        self.label.current_animation = self.label.walking_animation
        self.label.current_frame = 0
        self.label.loop_frame = 3
        self.animation_timer.start()

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setStartValue(self.pos())
        destination = random.randint(self.available_geometry.x(), self.available_geometry.x() + self.available_geometry.width() - self.width())
        self.anim.setEndValue(QtCore.QPoint(destination, self.pos().y()))
        distance = destination - self.pos().x()
        self.anim.setDuration(max(1, int(abs(distance / 0.06))))
        self.label.face_right = distance > 0
        self.anim.start()
        self.anim.finished.connect(self.done_animation)
    
    def done_animation(self):
        if self.dragging:
            return
        if hasattr(self, "pop_timer"):
            self.pop_timer.stop()
        self.in_animation = False
        self.balloonFall = False
        self.falling = False
        self.is_sleeping = False
        self.going_to_sleep = False
        self.animation_timer.stop()
        self.animation_timer.setInterval(200)
        self.label.setPixmap(self.label.walking_animation[0])
        self.event_timer.start(random.randint(1000, 5000))

    def heart(self):
        self.in_animation = True
        self.label.current_animation = self.label.heart_animation
        self.label.current_frame = 0
        self.label.loop_frame = 1
        self.event_timer.stop()
        self.animation_timer.start()
        self.heart_timer = QtCore.QTimer(self)
        self.heart_timer.setSingleShot(True)
        self.heart_timer.timeout.connect(self.done_animation)
        self.heart_timer.start(1600)

    def wave(self):
        self.in_animation = True
        self.label.current_animation = self.label.wave_animation
        self.label.current_frame = 0
        self.label.loop_frame = 3
        self.event_timer.stop()
        self.animation_timer.start()
        self.wave_timer = QtCore.QTimer(self)
        self.wave_timer.setSingleShot(True)
        self.wave_timer.timeout.connect(self.done_animation)
        self.wave_timer.start(2000)

    def eat(self):
        self.in_animation = True
        self.label.current_animation = self.label.eat_animation
        self.label.current_frame = 0
        self.label.loop_frame = 0
        self.event_timer.stop()
        self.animation_timer.start()
        self.eat_timer = QtCore.QTimer(self)
        self.eat_timer.setSingleShot(True)
        self.eat_timer.timeout.connect(self.done_animation)
        self.eat_timer.start(1800)

    def hit(self):
        self.in_animation = True
        self.label.current_animation = self.label.hit_animation
        self.label.current_frame = 0
        self.event_timer.stop()
        self.animation_timer.start()
        self.hit_timer = QtCore.QTimer(self)
        self.hit_timer.setSingleShot(True)
        self.hit_timer.timeout.connect(self.done_animation)
        self.hit_timer.start(1350)

    def fall(self):
        self.in_animation = True
        self.falling = True
        self.balloonFall = False
        self.label.current_animation = self.label.fall_animation
        self.label.current_frame = 0
        self.label.loop_frame = 0
        self.event_timer.stop()
        self.animation_timer.start()

    def balloon(self):
        self.in_animation = True
        self.balloonFall = True
        self.label.current_animation = self.label.balloon_animation
        self.label.current_frame = 0
        self.label.loop_frame = 5
        self.event_timer.stop()
        self.animation_timer.start()

    def pop(self):
        self.in_animation = True
        self.label.current_animation = self.label.pop_animation
        self.label.current_frame = 0
        self.event_timer.stop()
        self.animation_timer.start()
        self.pop_timer = QtCore.QTimer(self)
        self.pop_timer.setSingleShot(True)
        self.pop_timer.timeout.connect(self.fall)
        self.pop_timer.start(450)

    def toSleep(self):
        self.in_animation = True
        self.label.current_animation = self.label.to_sleep_animation
        self.label.current_frame = 0
        self.label.loop_frame = 0
        self.event_timer.stop()
        self.animation_timer.start()
        self.toSleep_timer = QtCore.QTimer(self)
        self.toSleep_timer.setSingleShot(True)
        self.toSleep_timer.start(1800)
        self.toSleep_timer.timeout.connect(self.sleep)

    def sleep(self):
        self.in_animation = True
        self.going_to_sleep = False
        self.is_sleeping = True
        self.label.current_animation = self.label.sleep_animation
        self.label.current_frame = 0
        self.label.loop_frame = 0
        self.event_timer.stop()
        self.animation_timer.start()

    def wakeup(self):
        self.in_animation = True
        self.is_sleeping = False
        self.label.current_animation = self.label.wakeup_animation
        self.label.current_frame = 0
        self.label.loop_frame = 0
        self.event_timer.stop()
        self.animation_timer.start()
        self.wakeup_timer = QtCore.QTimer(self)
        self.wakeup_timer.setSingleShot(True)
        self.wakeup_timer.timeout.connect(self.done_animation)
        self.wakeup_timer.start(1800)

    def work(self):
        self.in_animation = True
        self.going_to_sleep = False
        self.is_sleeping = False
        self.label.current_animation = self.label.work_animation
        self.label.current_frame = 0
        self.label.loop_frame = 6
        self.event_timer.stop()
        self.animation_timer.start()
        self.stopwatch.start()
        self.update_stopwatch()
        self.stopwatch_timer.start()
        self.stopwatch_label.show()

    def celebrate(self):
        self.in_animation = True
        self.label.current_animation = self.label.celebrate_animation
        self.label.current_frame = 0
        self.label.loop_frame = 0
        self.event_timer.stop()
        self.animation_timer.start()
        self.celebrate_timer = QtCore.QTimer(self)
        self.celebrate_timer.setSingleShot(True)
        self.celebrate_timer.timeout.connect(self.done_animation)
        self.celebrate_timer.start(1800)

    def done_work(self):    
        self.in_animation = True
        self.label.current_animation = self.label.done_work_animation
        self.label.current_frame = 0
        self.label.loop_frame = 0
        self.event_timer.stop()
        self.animation_timer.start()
        self.done_work_timer = QtCore.QTimer(self)
        self.done_work_timer.setSingleShot(True)
        self.done_work_timer.timeout.connect(self.celebrate)
        self.done_work_timer.start(1800)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton and not (self.falling or self.balloonFall):
            self.menu.popup(event.globalPosition().toPoint())
            return
        
        if event.button() == QtCore.Qt.LeftButton:
            if self.work_mode:
                return
            if hasattr(self, "toSleep_timer"):
                self.toSleep_timer.stop()
                self.going_to_sleep = False
                self.is_sleeping = False
            self.mousePressed = True
            self.mouseStartPos = event.globalPosition().toPoint()
            self.drag_position = event.globalPosition().toPoint() - self.pos()
            self.event_timer.stop()
            self.in_animation = True
            self.animation_timer.stop()
            if hasattr(self, 'anim'):
                self.anim.stop()
            for timer_name in ("heart_timer", "wave_timer", "eat_timer", "hit_timer", "wakeup_timer"):
                if hasattr(self, timer_name):
                    getattr(self, timer_name).stop()
            if self.going_to_sleep or self.is_sleeping:
                if hasattr(self, "toSleep_timer"):
                    self.toSleep_timer.stop()
                self.going_to_sleep = False
                self.is_sleeping = False

    def mouseMoveEvent(self, event):
        if not (event.buttons() & QtCore.Qt.LeftButton) or self.work_mode:
            return
        distance = (
            event.globalPosition().toPoint() - self.mouseStartPos
        ).manhattanLength()

        if not self.dragging and distance > QtWidgets.QApplication.startDragDistance():
            self.dragging = True
            self.label.current_animation = self.label.pickup_animation
            self.label.current_frame = 0
            self.animation_timer.start(50)

        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def mouseReleaseEvent(self, event):
        if self.work_mode:
            return
        if event.button() == QtCore.Qt.LeftButton:
            self.mousePressed = False
            if  self.dragging:
                self.in_animation = True
                self.dragging = False
                self.drag_position = None
                self.event_timer.stop()
                self.animation_timer.setInterval(200)
                self.balloon()

                self.anim = QPropertyAnimation(self, b"pos")
                self.anim.setStartValue(self.pos())
                self.anim.setEndValue(QtCore.QPoint(self.pos().x(), self.starting_y))
                distance = self.pos().y() - self.starting_y
                self.anim.setDuration(max(1, int(abs(distance / 0.1))))
                self.anim.start()
                self.anim.finished.connect(self.done_animation)
            elif self.balloonFall or self.falling:
                self.dragging = False
                self.drag_position = None
                self.in_animation = True
                self.event_timer.stop()
                if self.balloonFall:
                    self.animation_timer.setInterval(50)
                    self.pop()
                self.anim.stop()
                self.anim.setStartValue(self.pos())
                self.anim.setEndValue(QtCore.QPoint(self.pos().x(), self.starting_y))
                distance = self.pos().y() - self.starting_y
                self.anim.setDuration(max(1, int(abs(distance / 0.2))))
                self.anim.start()
                self.anim.finished.connect(self.done_animation)
            else: 
                if hasattr(self, "hit_timer"):
                    self.hit_timer.stop()
                self.dragging = False
                self.drag_position = None
                self.in_animation = True
                self.event_timer.stop()
                self.animation_timer.setInterval(150)
                self.hit()

class MySprite(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.loop_frame = 0

        self.walking_animation = load_file("Walk.png")
        self.heart_animation = load_file("Heart.png")
        self.heart_animation = self.heart_animation[:7:]
        self.wave_animation = load_file("Wave.png")
        self.eat_animation = load_file("Eat.png")   
        self.pickup_animation = load_file("Pickup.png")
        self.fall_animation = load_file("Fall.png")
        self.balloon_animation = load_file("Balloon.png")
        self.hit_animation = load_file("Hit.png")
        self.pop_animation = load_file("BalloonPop.png")
        self.to_sleep_animation = load_file("ToSleep.png")
        self.sleep_animation = load_file("Sleep.png")
        self.wakeup_animation = self.to_sleep_animation[::-1]
        self.work_animation = load_file("Work.png")
        self.done_work_animation = self.work_animation[::-1]
        self.celebrate_animation = load_file("Celebrate.png")

        self.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.setPixmap(self.walking_animation[0])

        self.face_right = False

    def next_frame(self):
        if self.current_animation is self.pickup_animation and self.current_frame >= 4:
            self.parent().animation_timer.stop()
            return

        if self.current_frame < len(self.current_animation) - 1:
            self.current_frame += 1
        else:
            self.current_frame = self.loop_frame

        frame = self.current_animation[self.current_frame]

        if self.face_right:
            frame = frame.transformed(QtGui.QTransform().scale(-1, 1))
        self.setPixmap(frame)
        self.resize(self.pixmap().size())

class MyMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)

        set_work_mode = self.addAction("Work Mode")
        set_work_mode.triggered.connect(self.parent().working)
        self.aboutToShow.connect(
            lambda: set_work_mode.setText("Stop Work Mode" if self.parent().work_mode else "Work Mode")
        )

if __name__ == "__main__":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "MiniMe"
    )
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(
        QtGui.QIcon(str(Path(__file__).parent / "assets" / "mini.ico"))
    )
    widget = MyWidget()
    label = MySprite(widget)
    widget.label = label
    widget.menu = MyMenu(widget)
    widget.animation_timer.timeout.connect(label.next_frame)
    widget.show()
    label.resize(label.pixmap().size())    
    label.show()
    sys.exit(app.exec())


