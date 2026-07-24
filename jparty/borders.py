from PyQt6.QtGui import QPainter, QBrush, QColor, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize, QTimer


from jparty.utils import resource_path


class Borders(object):
    def __init__(self, parent):
        super().__init__()
        self.left = self.create_widget(parent, -1)
        self.right = self.create_widget(parent, 1)
        self.__flash_states = []
        self.__flash_timer = QTimer(parent)
        self.__flash_timer.setInterval(200)
        self.__flash_timer.timeout.connect(self.__advance_flash)

    def __iter__(self):
        return iter([self.left, self.right])

    def create_widget(self, parent, d):
        return BorderWidget(parent, d)

    def flash(self):
        self.__flash_timer.stop()
        self.lights(False)
        self.__flash_states = [True, False]
        self.__flash_timer.start()

    def __advance_flash(self):
        self.lights(self.__flash_states.pop(0))
        if not self.__flash_states:
            self.__flash_timer.stop()

    def lights(self, val):
        for b in self:
            b.lights(val)


class HostBorders(Borders):
    def __init__(self, parent):
        super().__init__(parent)
        self.__hint_key = None
        self.__hints_visible = False
        self.__hint_timer = QTimer(parent)
        self.__hint_timer.setInterval(500)
        self.__hint_timer.timeout.connect(self.__toggle_hints)

    def create_widget(self, parent, d):
        return HostBorderWidget(parent, d)

    def __toggle_hints(self):
        self.__hints_visible = not self.__hints_visible
        for b in self:
            if self.__hints_visible:
                b.show_hints(self.__hint_key)
            else:
                b.hide_hints(self.__hint_key)

    def __set_hints(self, key, val):
        self.__hint_timer.stop()
        if self.__hint_key is not None:
            for b in self:
                b.hide_hints(self.__hint_key)

        self.__hint_key = key if val else None
        self.__hints_visible = False
        if val:
            self.__toggle_hints()
            self.__hint_timer.start()

    def show_settings_button(self, val):
        for b in self:
            b.show_settings_button(val)

    def arrowhints(self, val):
        for b in self:
            b.colors = val
            b.update()

        if val:
            self.__set_hints("arrow", True)
        else:
            self.__set_hints("arrow", False)

    def spacehints(self, val):
        self.__set_hints("space", val)


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
