from PyQt6.QtGui import QPainter, QBrush, QColor, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize


from jparty.utils import resource_path
import time
from threading import Thread, current_thread


class Borders(object):
    def __init__(self, parent):
        super().__init__()
        self.left = self.create_widget(parent, -1)
        self.right = self.create_widget(parent, 1)

    def __iter__(self):
        return iter([self.left, self.right])

    def create_widget(self, parent, d):
        return BorderWidget(parent, d)

    def __flash(self):
        self.lights(False)
        time.sleep(0.2)
        self.lights(True)
        time.sleep(0.2)
        self.lights(False)

    def flash(self):
        self.__flash_thread = Thread(target=self.__flash, name="flash")
        self.__flash_thread.start()

    def lights(self, val):
        for b in self:
            b.lights(val)


class HostBorders(Borders):
    def __init__(self, parent):
        super().__init__(parent)
        self.__active_thread = None

    def create_widget(self, parent, d):
        return HostBorderWidget(parent, d)

    def __flash_hints(self, key):
        while self.__active_thread == current_thread():
            for b in self:
                b.show_hints(key)
            time.sleep(0.5)
            for b in self:
                b.hide_hints(key)
            time.sleep(0.5)

    def buzz_hint(self):
        self.__buzz_hint_thread = Thread(target=self.__buzz_hint, name="buzz_hint")
        self.__buzz_hint_thread.start()

    def show_settings_button(self, val):
        for b in self:
            b.show_settings_button(val)

    def arrowhints(self, val):
        for b in self:
            b.colors = val
            b.update()

        if val:
            self.__active_thread = Thread(
                target=self.__flash_hints, args=("arrow",), name="arrow_hints"
            )
            self.__active_thread.start()
        else:
            self.__active_thread = None
            for b in self:
                b.hide_hints("arrow")

    def spacehints(self, val):
        if val:
            self.__active_thread = Thread(
                target=self.__flash_hints, args=("space",), name="space_hints"
            )
            self.__active_thread.start()
        else:
            self.__active_thread = None
            for b in self:
                b.hide_hints("space")

    def closeEvent(self, event):
        super().closeEvent(event)
        self.__active_hint = None


class BorderWidget(QWidget):
    def __init__(self, parent, d):
        super().__init__(parent)
        self.d = d
        self.__lit = False
        self.show()

    def lights(self, val):
        self.__lit = val
        self.update()

    def sizeHint(self):
        return QSize()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.__lit:
            qp.setBrush(QBrush(QColor("white")))
            qp.drawRect(self.rect())


class HostBorderWidget(BorderWidget):
    def __init__(self, parent, d):
        super().__init__(parent, d)
        self.layout = QVBoxLayout()
        self.hint_label = QLabel(self)

        self.layout.addWidget(self.hint_label)
        self.setLayout(self.layout)

        self.__hint_images = {
            "space": QPixmap(resource_path("space.png")),
            "arrow": QPixmap(
                resource_path(("right" if d == 1 else "left") + "-arrow.png")
            ),
        }

        self.colors = False
        self.show()

    def show_hints(self, key):
        self.hint_label.setPixmap(
            self.__hint_images[key].scaled(
                self.size() * 0.9,
                Qt.AspectRatioMode.KeepAspectRatio,
                transformMode=Qt.TransformationMode.SmoothTransformation,
            )
        )

    def hide_hints(self, key):
        self.hint_label.setPixmap(QPixmap())

    def resizeEvent(self, event):
        margin = int(self.width() * 0.05)
        self.hint_label.setMargin(margin)

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter()
        qp.begin(self)
        if self.colors:
            qp.setBrush(QBrush(QColor("#ff0000" if self.d == 1 else "#33cc33")))
            qp.drawRect(self.rect())
