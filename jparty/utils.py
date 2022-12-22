import simpleaudio as sa

import requests
from threading import Thread
import logging
import re
import os
import sys
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QImage,
    QColor,
    QFont,
    QPalette,
    QPixmap,
    QTextDocument,
    QTextOption,
    QGuiApplication,
    QFontMetrics,
    QTransform
)
from PyQt6.QtWidgets import *  # QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt6.QtCore import (
    Qt,
    QRectF,
    QRect,
    QPoint,
    QPointF,
    QTimer,
    QRect,
    QSize,
    QSizeF,
    QMargins,
)
from PyQt6.sip import delete


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        print("USING MEIPASS")
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

    @property
    def is_playing():
        return self.__play_obj.is_repeating()

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


def permission_error():
    button = QMessageBox.critical(
        None,
        "Permission Error",
        "JParty encountered a permissions error when trying to listen on port 80.",
        buttons=QMessageBox.StandardButton.Abort,
        defaultButton=QMessageBox.StandardButton.Abort,
    )

def check_internet():
    pass
    # check internet connection
    # try:
    #     r = requests.get(f"http://www.j-archive.com/")
    # except requests.exceptions.ConnectionError as e:  # This is the correct syntax
    #     button = QMessageBox.critical(
    #         None,
    #         "Cannot connect!",
    #         "JParty cannot connect to the J-Archive. Please check your internet connection.",
    #         buttons=QMessageBox.StandardButton.Abort,
    #         defaultButton=QMessageBox.StandardButton.Abort,
    #     )
    #     exit(1)

"""add shadow to widget. Radius is proportion of widget height"""
def add_shadow(widget, radius=0.1, offset=3):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(widget.height())
    shadow.setColor(QColor("black"))
    shadow.setOffset(offset)
    widget.setGraphicsEffect(shadow)



class AutosizeWidget(object):

    def getInitialSize(self):
        if callable(self.initialSize):
            return self.initialSize()
        else:
            return self.initialSize


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

    def autofitsize(self, stepsize=1):

        font = self.font()
        rect = self.rect()
        text = self.plaintext()

        font.setPointSize(self.getInitialSize())
        size = font.pointSize()

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

            # logging.warn(f"Nothing fit! (text='{text}')")
            # print(f"Nothing fit! (text='{text}')")

        return size

class DynamicLabel(QLabel, AutosizeWidget):
    def __init__(self, text, initialSize, parent=None):
        super().__init__( text, parent )
        self.initialSize = initialSize
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.autoresize()

    def flags(self):
        flags = 0
        if self.wordWrap():
            flags |= Qt.TextFlag.TextWordWrap

        flags |= self.alignment()

        return flags

    def setText(self, text):
        super().setText(text)
        self.autoresize()



class DynamicButton(QPushButton, AutosizeWidget):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.initialSize = lambda : self.height() * 0.5
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.autoresize()

    def flags(self):
        return 0


