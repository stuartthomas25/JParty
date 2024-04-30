from PyQt6.QtGui import QPainter, QBrush, QImage, QFont, QPalette, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QSizePolicy,
    QMessageBox,
    QLabel,
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal

import qrcode
import time
from threading import Thread
import logging

from jparty.version import version
from jparty.retrieve import get_game, get_random_game
from jparty.utils import resource_path, add_shadow, DynamicLabel, DynamicButton
from jparty.helpmsg import helpmsg
from jparty.style import WINDOWPAL


class Image(qrcode.image.base.BaseImage):
    """QR code image widget"""

    def __init__(self, border, width, box_size):
        self.border = border
        self.width = width
        self.box_size = box_size
        size = (width + border * 2) * box_size
        self._image = QImage(size, size, QImage.Format.Format_RGB16)
        self._image.fill(WINDOWPAL.color(QPalette.ColorRole.Window))

    def pixmap(self):
        return QPixmap.fromImage(self._image)

    def drawrect(self, row, col):
        painter = QPainter(self._image)
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size,
            self.box_size,
            Qt.GlobalColor.black,
        )

    def save(self, stream, kind=None):
        pass


class StartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon = QPixmap(resource_path("icon.png"))
        self.icon_label = DynamicLabel("", 0, self)

        add_shadow(self, radius=0.2)
        self.setPalette(WINDOWPAL)

        self.icon_layout = QHBoxLayout()
        self.icon_layout.addStretch()
        self.icon_layout.addWidget(self.icon_label)
        self.icon_layout.addStretch()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(QBrush(WINDOWPAL.color(QPalette.ColorRole.Window)))
        qp.drawRect(self.rect())

    def resizeEvent(self, event):
        icon_size = self.icon_label.height()
        self.icon_label.setPixmap(
            self.icon.scaled(
                icon_size,
                icon_size,
                transformMode=Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.icon_label.setMaximumWidth(icon_size)


class Welcome(StartWidget):
    gameid_trigger = pyqtSignal(str)
    summary_trigger = pyqtSignal(str)

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.title_font = QFont()
        self.title_font.setBold(True)

        self.title_label = DynamicLabel("JParty!", lambda: self.height() * 0.1, self)
        self.title_label.setFont(self.title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.version_label = DynamicLabel(
            f"version {version}", lambda: self.height() * 0.03
        )
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet("QLabel { color : grey}")

        select_layout = QHBoxLayout()

        template_url = "https://docs.google.com/spreadsheets/d/1_vBBsWn-EVc7npamLnOKHs34Mc2iAmd9hOGSzxHQX0Y/edit#gid=0"
        gameid_text = f'Game ID (from J-Archive URL)<br>or <a href="{template_url}">GSheet ID for custom game</a>'
        self.gameid_label = DynamicLabel(gameid_text, lambda: self.height() * 0.1, self)
        self.gameid_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.gameid_label.setOpenExternalLinks(True)

        self.textbox = QLineEdit(self)
        self.textbox.textChanged.connect(self.show_summary)
        f = self.textbox.font()
        self.textbox.setFont(f)

        button_layout = QVBoxLayout()
        self.start_button = DynamicButton("Start!", self)
        self.start_button.clicked.connect(self.game.start_game)
        self.start_button.setEnabled(False)

        self.rand_button = DynamicButton("Random", self)
        self.rand_button.clicked.connect(self.random)

        button_layout.addWidget(self.start_button, 10)
        button_layout.addStretch(1)
        button_layout.addWidget(self.rand_button, 10)

        select_layout.addStretch(5)
        select_layout.addWidget(self.gameid_label, 40)
        select_layout.addStretch(2)
        select_layout.addWidget(self.textbox, 40)
        select_layout.addStretch(2)
        select_layout.addLayout(button_layout, 20)
        select_layout.addStretch(5)

        self.summary_label = DynamicLabel("", lambda: self.height() * 0.04, self)
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.quit_button = DynamicButton("Quit", self)
        self.quit_button.clicked.connect(self.game.close)

        self.help_button = DynamicButton("Show help", self)
        self.help_button.clicked.connect(self.show_help)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch(5)
        footer_layout.addWidget(self.quit_button, 3)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.help_button, 3)
        footer_layout.addStretch(5)

        main_layout.addStretch(3)
        main_layout.addLayout(self.icon_layout, 6)
        main_layout.addWidget(self.title_label, 3)
        main_layout.addWidget(self.version_label, 1)
        main_layout.addStretch(1)
        main_layout.addLayout(select_layout, 5)
        main_layout.addStretch(1)
        main_layout.addWidget(self.summary_label, 5)
        main_layout.addLayout(footer_layout, 3)
        main_layout.addStretch(3)

        self.gameid_trigger.connect(self.set_gameid)
        self.summary_trigger.connect(self.set_summary)

        self.setLayout(main_layout)

        self.show()

    def show_help(self):
        logging.info("Showing help")
        msgbox = QMessageBox(
            QMessageBox.Icon.NoIcon,
            "JParty Help",
            helpmsg,
            QMessageBox.StandardButton.Ok,
            self,
        )
        msgbox.exec()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        textbox_height = int(self.gameid_label.height() * 0.8)
        self.textbox.setMinimumSize(QSize(0, textbox_height))
        f = self.textbox.font()
        f.setPixelSize(int(textbox_height * 0.9))
        self.textbox.setFont(f)

    def __random(self):
        try:
            while True:
                game_id = get_random_game()
                logging.info(f"GAMEID {game_id}")
                self.game.data = get_game(game_id)
                if self.game.valid_game():
                    break
                else:
                    time.sleep(0.25)

            self.gameid_trigger.emit(str(game_id))
            self.summary_trigger.emit(self.game.data.date + "\n" + self.game.data.comments)

        except Exception as e:
            logging.error(e)
            self.summary_trigger.emit("Cannot get game")

    def random(self, checked):
        self.summary_trigger.emit("Loading...")
        t = Thread(target=self.__random)
        t.start()

    def __show_summary(self):
        game_id = self.textbox.text()
        try:
            self.game.data = get_game(game_id)
            if self.game.valid_game():
                self.summary_trigger.emit(
                    self.game.data.date + "\n" + self.game.data.comments
                )
            else:
                self.summary_trigger.emit("Game has blank questions")

        except Exception as e:
            logging.error(e)
            self.summary_trigger.emit("Cannot get game")

        self.check_start()

    def set_summary(self, text):
        self.summary_label.setText(text)

    def set_gameid(self, text):
        self.textbox.setText(text)

    def show_summary(self, text=None):
        self.summary_trigger.emit("Loading...")
        t = Thread(target=self.__show_summary)
        t.start()

        self.check_start()

    def check_start(self):
        if self.game.startable():
            self.start_button.setEnabled(True)
        else:
            self.start_button.setEnabled(False)

    def restart(self):
        self.show_summary(self)


class QRWidget(StartWidget):
    def __init__(self, host, parent=None):
        super().__init__(parent)

        self.font = QFont()
        self.font.setPointSize(30)

        main_layout = QVBoxLayout()

        self.hint_label = DynamicLabel("Scan for Buzzer:", self.start_fontsize, self)
        self.hint_label.setFont(self.font)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.qrlabel = QLabel(self)
        self.qrlabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.url = "http://" + host
        self.url_label = DynamicLabel(self.url, self.start_fontsize, self)
        self.url_label.setFont(self.font)
        self.url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addStretch(1)
        main_layout.addLayout(self.icon_layout, 5)
        main_layout.addWidget(self.hint_label, 2)
        main_layout.addWidget(self.qrlabel, 5)
        main_layout.addWidget(self.url_label, 2)
        main_layout.addStretch(1)

        self.setLayout(main_layout)

        self.show()

    def start_fontsize(self):
        return 0.1 * self.width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.qrlabel.setPixmap(
            qrcode.make(
                self.url, image_factory=Image, box_size=max(self.height() / 50, 1)
            ).pixmap()
        )

    def restart(self):
        pass
