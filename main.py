from ast import walk
import sys
import random
import ctypes
from ctypes import wintypes
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QPropertyAnimation


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
        elif self.dragging or self.mousePressed:
            return
        elif self.idle_time > 5000 and not self.is_sleeping and not self.going_to_sleep:
            self.event_timer.stop()
            self.in_animation = True
            self.going_to_sleep = True
            self.animation_timer.stop()
            if hasattr(self, 'anim') and not self.balloonFall:
                self.anim.stop()
            for timer_name in ("heart_timer", "wave_timer", "eat_timer"):
                if hasattr(self, timer_name):
                    getattr(self, timer_name).stop()
            self.label.current_animation = self.label.walking_animation
            self.label.current_frame = 0
            self.label.loop_frame = 2
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
            if hasattr(self, "toSleepTimer"):
                self.toSleep_timer.stop()
            self.is_sleeping = False
            self.going_to_sleep = False
            self.event_timer.stop()
            self.in_animation = True
            self.animation_timer.stop()
            if hasattr(self, 'anim') and not self.balloonFall:
                self.anim.stop()
            for timer_name in ("heart_timer", "wave_timer", "eat_timer"):
                if hasattr(self, timer_name):
                    getattr(self, timer_name).stop()
            self.wakeup()

    def walk(self):
        self.in_animation = True
        self.event_timer.stop()
        self.label.current_animation = self.label.walking_animation
        self.label.current_frame = 0
        self.label.loop_frame = 2
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
        self.balloonFall = False
        self.falling = True
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
        self.label.current_animation = self.label.toSleep_animation
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
        self.label.current_animation = self.label.wakeup_animation
        self.label.current_frame = 0
        self.label.loop_frame = 0
        self.event_timer.stop()
        self.animation_timer.start()
        self.wakeup_timer = QtCore.QTimer(self)
        self.wakeup_timer.setSingleShot(True)
        self.wakeup_timer.timeout.connect(self.done_animation)
        self.wakeup_timer.start(1800)
        
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
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
            for timer_name in ("heart_timer", "wave_timer", "eat_timer"):
                if hasattr(self, timer_name):
                    getattr(self, timer_name).stop()
            if self.going_to_sleep or self.is_sleeping:
                self.toSleep_timer.stop()
                self.going_to_sleep = False
                self.is_sleeping = False

    def mouseMoveEvent(self, event):
        if not (event.buttons() & QtCore.Qt.LeftButton):
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

        walk_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "Walk.png")
        )

        walk_frame_size = walk_sprite_sheet.width() // 3
        walk_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        walk_frame_positions = walk_frame_positions[:7]
        self.walking_animation = [
            walk_sprite_sheet.copy(column * walk_frame_size, row * walk_frame_size, walk_frame_size, walk_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in walk_frame_positions
        ]       

        self.walk_current_frame = 0
        self.walk_loop_frame = 1

        heart_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "Heart.png")
        )

        heart_frame_size = heart_sprite_sheet.width() // 3
        heart_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        heart_frame_positions = heart_frame_positions[:7]
        self.heart_animation = [
            heart_sprite_sheet.copy(column * heart_frame_size, row * heart_frame_size, heart_frame_size, heart_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in heart_frame_positions
        ]

        wave_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "Wave.png")
        )

        wave_frame_size = wave_sprite_sheet.width() // 3
        wave_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        wave_frame_positions = wave_frame_positions[:5]
        self.wave_animation = [
            wave_sprite_sheet.copy(column * wave_frame_size, row * wave_frame_size, wave_frame_size, wave_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in wave_frame_positions
        ]

        eat_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "Eat.png")
        )

        eat_frame_size = eat_sprite_sheet.width() // 3
        eat_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        self.eat_animation = [
            eat_sprite_sheet.copy(column * eat_frame_size, row * eat_frame_size, eat_frame_size, eat_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in eat_frame_positions
        ]

        pickup_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "Pickup.png")
        )

        pickup_frame_size = pickup_sprite_sheet.width() // 3
        pickup_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        self.pickup_animation = [
            pickup_sprite_sheet.copy(column * pickup_frame_size, row * pickup_frame_size, pickup_frame_size, pickup_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in pickup_frame_positions
        ]

        fall_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "Fall.png")
        )

        fall_frame_size = fall_sprite_sheet.width() // 3
        fall_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        fall_frame_positions = fall_frame_positions[3:7]
        self.fall_animation = [
            fall_sprite_sheet.copy(column * fall_frame_size, row * fall_frame_size, fall_frame_size, fall_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in fall_frame_positions
        ]

        balloon_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "Balloon.png")
        )

        balloon_frame_size = balloon_sprite_sheet.width() // 3
        balloon_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        self.balloon_animation = [
            balloon_sprite_sheet.copy(column * balloon_frame_size, row * balloon_frame_size, balloon_frame_size, balloon_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in balloon_frame_positions
        ]

        hit_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "Hit.png")
        )

        hit_frame_size = hit_sprite_sheet.width() // 3
        hit_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        self.hit_animation = [
            hit_sprite_sheet.copy(column * hit_frame_size, row * hit_frame_size, hit_frame_size, hit_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in hit_frame_positions
        ]

        pop_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "BalloonPop.png")
        )

        pop_frame_size = pop_sprite_sheet.width() // 3
        pop_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        self.pop_animation = [
            pop_sprite_sheet.copy(column * pop_frame_size, row * pop_frame_size, pop_frame_size, pop_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in pop_frame_positions
        ]

        toSleep_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "ToSleep.png")
        )

        toSleep_frame_size = toSleep_sprite_sheet.width() // 3
        toSleep_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        self.toSleep_animation = [
            toSleep_sprite_sheet.copy(column * toSleep_frame_size, row * toSleep_frame_size, toSleep_frame_size, toSleep_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in toSleep_frame_positions
        ]

        wakeup_frame_positions = toSleep_frame_positions[::-1]
        self.wakeup_animation = [
            toSleep_sprite_sheet.copy(column * toSleep_frame_size, row * toSleep_frame_size, toSleep_frame_size, toSleep_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in wakeup_frame_positions
        ]


        Sleep_sprite_sheet = QtGui.QPixmap(
            str(Path(__file__).parent / "assets" / "Sleep.png")
        )

        sleep_frame_size = Sleep_sprite_sheet.width() // 3
        sleep_frame_positions = [(column, row) for row in range(3) for column in range(3)]
        self.sleep_animation = [
            Sleep_sprite_sheet.copy(column * sleep_frame_size, row * sleep_frame_size, sleep_frame_size, sleep_frame_size)
            .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
            for column, row in sleep_frame_positions
        ]

        self.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.setPixmap(self.walking_animation[self.walk_current_frame])

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

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()
    label = MySprite(widget)
    widget.label = label
    widget.animation_timer.timeout.connect(label.next_frame)
    widget.show()
    label.resize(label.pixmap().size())    
    label.show()
    sys.exit(app.exec())


