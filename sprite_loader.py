from pathlib import Path
from PySide6 import QtCore, QtGui

def load_file(filename):
    sprite_sheet = QtGui.QPixmap(str(Path(__file__).parent / "assets" / filename))
    frame_size = sprite_sheet.width() // 3        
    frame_positions = [(column, row) for row in range(3) for column in range (3)]
    animation = [
        sprite_sheet.copy(column * frame_size, row * frame_size, frame_size, frame_size)
        .scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
        for column, row in frame_positions
    ]
    return animation


        