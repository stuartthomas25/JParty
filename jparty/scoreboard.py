from PyQt6.QtGui import QPainter, QPixmap, QImage, QPalette, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QSize

import time
from threading import Thread
from base64 import urlsafe_b64decode

from jparty.style import MyLabel
from jparty.utils import resource_path


class NameLabel(MyLabel):
    name_aspect_ratio = 1.3422

    def __init__(self, name, parent):
        self.signature = None
        super().__init__("", self.startNameFontSize, parent)

        if name[:21] == "data:image/png;base64":
            i = QImage()
            i.loadFromData(urlsafe_b64decode(name[22:]), "PNG")
            self.signature = QPixmap.fromImage(i)
        else:
            self.setText(name)

        self.setGraphicsEffect(None)

    def startNameFontSize(self):
        return self.height() * 0.2

    def resizeEvent(self, event):
        if self.signature is not None:
            self.setPixmap(
                self.signature.scaled(
                    self.height() * NameLabel.name_aspect_ratio,
                    self.height(),
                    transformMode=Qt.TransformationMode.SmoothTransformation,
                )
            )


class PlayerWidget(QWidget):
    aspect_ratio = 0.732
    margin = 0.05

    def __init__(self, game, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.game = game
        self.__buzz_hint_thread = None
        self.__flash_thread = None
        self.__light_thread = None

        self.name_label = NameLabel(player.name, self)

        self.score_label = MyLabel("$0", self.startScoreFontSize, self)

        self.resizeEvent(None)
        self.update_score()

        self.setMouseTracking(True)

        self.main_background = QPixmap(resource_path("player.png"))
        self.active_background = QPixmap(resource_path("player_active.png"))
        self.lights_backgrounds = [
            QPixmap(resource_path(f"player_lights{i}.png")) for i in range(1, 6)
        ]
        self.background = self.main_background

        self.highlighted = False

        layout = QVBoxLayout()
        layout.addStretch(4)
        layout.addWidget(self.score_label, 10)
        layout.addStretch(11)
        layout.addWidget(self.name_label, 31)
        layout.addStretch(10)

        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)

        self.setLayout(layout)

        self.show()

    def sizeHint(self):
        h = self.height()
        return QSize(h * PlayerWidget.aspect_ratio, h)

    def minimumSizeHint(self):
        return QSize()

    def startScoreFontSize(self):
        return self.height() * 0.2

    def resizeEvent(self, event):
        m = PlayerWidget.margin
        self.setContentsMargins(self.width() * m, 0, self.width() * m, 0)

    def set_lights(self, val):
        self.background = self.active_background if val else self.main_background
        self.update()

    def __buzz_hint(self):
        self.set_lights(True)
        time.sleep(0.25)
        self.set_lights(False)

    def buzz_hint(self):
        self.__buzz_hint_thread = Thread(target=self.__buzz_hint, name="buzz_hint")
        self.__buzz_hint_thread.start()

    def update_score(self):
        score = self.player.score
        palette = self.score_label.palette()
        if score < 0:
            palette.setColor(QPalette.ColorRole.WindowText, QColor("red"))
        else:
            palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
        self.score_label.setPalette(palette)

        self.score_label.setText(f"{score:,}")

    def run_lights(self):
        self.__light_thread = Thread(target=self.__lights, name="lights")
        self.__light_thread.start()

    def stop_lights(self):
        self.__light_thread = None
        self.set_lights(False)
        self.update()

    def __lights(self):
        for img in self.lights_backgrounds:
            self.background = img
            self.update()
            time.sleep(1.0)
            if self.__light_thread is None:  # provide stopability
                return None

        self.set_lights(True)
        self.update()

    def mousePressEvent(self, event):
        if self.game.soliciting_player:
            self.game.get_dd_wager(self.player)
            return None

        self.game.adjust_score(self.player)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap(self.rect(), self.background)
        qp.end()

    def leaveEvent(self, event):
        if self.game.soliciting_player:
            self.set_lights(False)

    def enterEvent(self, event):
        if self.game.soliciting_player:
            self.set_lights(True)


class ScoreBoard(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)

        self.game = game

        # self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.player_widgets = []

        self.player_layout = QHBoxLayout()
        self.player_layout.addStretch()
        self.setLayout(self.player_layout)
        self.show()

    def minimumHeight(self):
        return 0.2 * self.width()

    def refresh_players(self):

        for pw in list(self.player_widgets):  # copy list so we can remove elements
            if pw.player not in self.game.players:
                i = self.player_layout.indexOf(pw)
                self.player_layout.takeAt(i + 1)  # remove stretch
                self.player_layout.takeAt(i)
                self.player_widgets.remove(pw)
                pw.deleteLater()

        for (i, p) in enumerate(self.game.players):
            if not any(pw.player is p for pw in self.player_widgets):
                pw = PlayerWidget(self.game, p, self)
                self.player_layout.insertWidget(2 * i + 1, pw)
                self.player_layout.insertStretch(2 * i + 2)
                self.player_widgets.append(pw)

        self.update()

        # self.setLayout(self.player_layout)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap(self.rect(), QPixmap(resource_path("pedestal.png")))
        qp.end()
