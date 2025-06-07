import simpleaudio as sa

from threading import Thread
import re
import os
import sys


from PyQt6.QtGui import QColor, QFontMetrics
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QSize


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS

    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, "data", relative_path)


class SongPlayer(object):
    def __init__(self):
        super().__init__()
        self.__wave_obj = sa.WaveObject.from_wave_file(resource_path("intro.wav"))
        self.__final = sa.WaveObject.from_wave_file(resource_path("final.wav"))
        self.__play_obj = None
        self.__repeating = False
        self.__repeat_thread = None

    def play(self, repeat=False):
        self.__repeating = repeat
        self.__play_obj = self.__wave_obj.play()
        if repeat:
            self.__repeat_thread = Thread(target=self.__repeat)
            self.__repeat_thread.start()

    def final(self, repeat=False):
        self.__repeating = repeat
        self.__play_obj = self.__final.play()
        if repeat:
            self.__repeat_thread = Thread(target=self.__repeat)
            self.__repeat_thread.start()

    def stop(self):
        self.__repeating = False
        self.__play_obj.stop()

    def __repeat(self):
        while True:
            self.__play_obj.wait_done()
            if not self.__repeating:
                break
            self.__play_obj = self.__wave_obj.play()


class CompoundObject(object):
    def __init__(self, *objs):
        self.__objs = list(objs)

    def __setattr__(self, name, value):
        if name[0] == "_":
            self.__dict__[name] = value
        else:
            for obj in self.__objs:
                setattr(obj, name, value)

    def __getattr__(self, name):
        ret = CompoundObject(*[getattr(obj, name) for obj in self.__objs])
        return ret

    def __iadd__(self, display):
        self.__objs.append(display)
        return self

    def __call__(self, *args, **kwargs):
        return CompoundObject(*[obj(*args, **kwargs) for obj in self.__objs])

    def __repr__(self):
        return "CompoundObject(" + ", ".join([repr(o) for o in self.__objs]) + ")"


"""add shadow to widget. Radius is proportion of widget height"""


def add_shadow(widget, radius=0.1, offset=3):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(widget.height())
    shadow.setColor(QColor("black"))
    shadow.setOffset(offset)
    widget.setGraphicsEffect(shadow)


class AutosizeWidget(object):
    """This class is a mixin which must be inherited with a QWidget with a `text()` method."""

    def __init__(self, *args, **kwargs):
        self.autosize_margins = (0.0, 0.0, 0.0, 0.0)  # as percentage of size
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.autoresize()

    def sizeHint(self):
        return QSize()

    def minimumSizeHint(self):
        return QSize()

    def heightForWidth(self, w):
        return -1

    def resizeEvent(self, event):
        self.autoresize()

    def autoresize(self):
        if self.size().height() == 0 or self.text() == "":
            return None

        fontsize = self.autofitsize()
        font = self.font()
        font.setPixelSize(fontsize)
        self.setFont(font)

    def plaintext(self):
        text = self.text()
        text = re.sub("<br>", "\n", text)
        text = re.sub("<[^>]*>", "", text)
        return text

    def setAutosizeMargins(self, *args):
        """
        set the dynamic sizing margins.
        ---
        if 1 arg, set all margins,
        if 2 args, set width and height margins
        if 4 args, set left, top, right and bottom margins
        """
        if len(args) == 1:
            self.autosize_margins = (args[0], args[0], args[0], args[0])
        elif len(args) == 2:
            self.autosize_margins = (args[0], args[1], args[0], args[1])
        elif len(args) == 4:
            self.autosize_margins = (args[0], args[1], args[2], args[3])
        else:
            raise Exception("Need 1, 2, or 4 arguments")

    def autofitsize(self, stepsize=1):

        font = self.font()

        ml, mt, mr, md = self.autosize_margins
        rect = self.rect().adjusted(
            int(self.width() * ml),
            int(self.height() * mt),
            int(-self.width() * mr),
            int(-self.height() * mt),
        )

        text = self.plaintext()

        font.setPixelSize(int(self.initialSize()))
        size = font.pixelSize()

        def fullrect(font):
            fm = QFontMetrics(font)
            return fm.boundingRect(rect, self.flags(), text)

        newrect = fullrect(font)
        if not rect.contains(newrect):
            while size > 2:
                size -= stepsize
                font.setPixelSize(size)
                newrect = fullrect(font)
                if rect.contains(newrect):
                    return font.pixelSize()

        return size


class DynamicLabel(QLabel, AutosizeWidget):
    def __init__(self, text, initialSize, parent=None):
        self.__initialSize = initialSize
        super().__init__(text, parent)

    def flags(self):
        flags = 0
        if self.wordWrap():
            flags |= Qt.TextFlag.TextWordWrap

        flags |= self.alignment()

        return flags

    def resizeEvent(self, event):
        AutosizeWidget.resizeEvent(self, event)

    def setText(self, text):
        ss = self.styleSheet()
        self.setStyleSheet("color: transparent;")
        super().setText(text)
        self.autoresize()
        self.setStyleSheet(ss)

    def initialSize(self):
        if callable(self.__initialSize):
            return self.__initialSize()
        else:
            return self.__initialSize


class DynamicButton(QPushButton, AutosizeWidget):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

    def resizeEvent(self, event):
        AutosizeWidget.resizeEvent(self, event)

    def setText(self, text):
        super().setText(text)
        self.autoresize()

    def initialSize(self):
        return self.height() * 0.5

    def flags(self):
        return 0


class DDWagerDialog(QDialog):
    def __init__(self, parent=None, max_wager=42):
        super().__init__(parent)
        self.setWindowTitle("Daily Double Wager")
        self.value = None
        self.max_wager = max_wager

        # Create layout
        layout = QVBoxLayout(self)

        # Input label and line edit
        self.label = QLabel("Wager:", self)
        layout.addWidget(self.label)

        self.input_field = QLineEdit(self)
        self.input_field.returnPressed.connect(self.submit)
        layout.addWidget(self.input_field)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Predefined value button
        self.truedd_button = QPushButton("True Daily Double!", self)
        self.truedd_button.clicked.connect(self.submit_predefined)
        buttons_layout.addWidget(self.truedd_button)

        # Submit button
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.submit)
        buttons_layout.addWidget(self.submit_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)
        layout.addLayout(buttons_layout)

    def submit(self):
        """Handle submission of the entered value."""
        try:
            self.value = int(self.input_field.text())
            if self.value < 0 or self.value > self.max_wager:
                raise ValueError()
            self.accept()
        except ValueError:
            self.label.setText(
                f"Please enter a whole number between 0 and {self.max_wager}"
            )
            self.label.setStyleSheet("color: red;")

    def submit_predefined(self):
        """Handle submission of the predefined value."""
        self.value = self.max_wager
        self.accept()

    @staticmethod
    def getInt(parent=None, max_wager=1000):
        """Static method to get an integer from the user."""
        dialog = DDWagerDialog(parent, max_wager)
        result = dialog.exec()
        return dialog.value, result == QDialog.DialogCode.Accepted
