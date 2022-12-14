import sys
import os
from random import shuffle
from PyQt6.QtGui import (
    QImage,
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFont,
    QMovie,
    QPixmap,
    QDesktopServices,
    QPalette,
    QGuiApplication,
    QFontDatabase,
    QColor,
)

import requests


# from PyQt6.QtMultimedia import QSound
from PyQt6.QtWidgets import *  # QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt6.QtCore import Qt, QRectF, QRect, QPoint, QTimer, QSize, QDir, QMargins, pyqtSignal
import logging

import pickle
from threading import Thread, active_count
from random import choice
import time
import subprocess
import qrcode

import threading
from functools import partial

# from .data_rc import *
from .retrieve import get_game, get_game_sum, get_random_game
from .controller import BuzzerController
from .boardwindow import DisplayWindow
from .game import Player, Game
from .constants import DEBUG
from .utils import SongPlayer, resource_path
from .version import version
from .logger import qt_exception_hook


def updateUI(f):
    def wrapper(self, *args):
        ret = f(self, *args)
        self.update()
        return ret

    return wrapper


MOVIEWIDTH = 64
LABELFONTSIZE = 15
OVERLAYFONTSIZE = 40



class Image(qrcode.image.base.BaseImage):
    def __init__(self, border, width, box_size):
        self.border = border
        self.width = width
        self.box_size = box_size
        size = (width + border * 2) * box_size
        self._image = QImage(
            size, size, QImage.Format.Format_RGB16)
        self._image.fill(Qt.GlobalColor.white)

    def pixmap(self):
        return QPixmap.fromImage(self._image)

    def drawrect(self, row, col):
        painter = QPainter(self._image)
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size, self.box_size,
            Qt.GlobalColor.black)

    def save(self, stream, kind=None):
        pass




class Welcome(QMainWindow):
    buzz_hint_trigger = pyqtSignal(int)

    def __init__(self, SC):
        super().__init__()
        self.socket_controller = SC
        self.socket_controller.welcome_window = self
        self.title = f"JParty! (v {version})"
        self.left = 10
        self.top = 10
        self.width = 500
        self.height = 320
        self.all_games = None
        self.valid_game = False
        self.gamedata = None
        self.song_player = SongPlayer()
        self.host_overlay = None

        self.buzz_hint_trigger.connect(self.buzz_hint)

        # logging.info(final_song.fileName())
        # final_song.play()
        # logging.info("play")

        # self.song.setLoops(QSound.Infinite)
        # self.song.play()
        if not DEBUG:
            self.song_player.play(repeat=True)
        else:
            self.song_player = None

        self.icon_label = QLabel(self)
        self.startButton = QPushButton("Start!", self)

        self.randButton = QPushButton("Random", self)
        self.summary_label = QLabel("", self)
        self.summary_label.setWordWrap(True)

        self.help_checkbox = QCheckBox("Show help", self)

        self.textbox = QLineEdit(self)
        self.gameid_label = QLabel("Game ID:\n(from J-Archive URL) or", self)
        self.gameid_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.custom_label = QLabel("GSheet ID for custom game", self)
        self.custom_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # makes self.custom_label a link going to template
        self.linkTemplate = '<a href={0}>{1}</a>'
        self.custom_label.setOpenExternalLinks(True)
        self.template_URL = "https://docs.google.com/spreadsheets/d/1_vBBsWn-EVc7npamLnOKHs34Mc2iAmd9hOGSzxHQX0Y/edit#gid=0"
        self.custom_label.setText(self.linkTemplate.format(self.template_URL, "GSheet ID for custom game"))

        # self.player_heading = QLabel("Players:", self)
        # self.player_labels = [QLabel(self) for _ in range(3)]

        self.monitor_error = QLabel("JParty requires two seperate monitors", self)

        self.show()
        self.initUI()

        if os.path.exists(".bkup"):
            logging.info("backup")
            self.run_game(pickle.load(open(".bkup", "rb")))

    def show_overlay(self):
        if not DEBUG:
            self.host_overlay = HostOverlay(self.socket_controller.host())
            self.windowHandle().setScreen(QApplication.instance().screens()[1])
            self.host_overlay.showNormal()

    def _random(self):
        complete = False
        while not complete:
            game_id = get_random_game()
            logging.info(f"GAMEID {game_id}")
            complete = all(b.complete for b in get_game(game_id).rounds)


        self.textbox.setText(str(game_id))
        self.textbox.show()

    def random(self, checked):
        self.summary_label.setText("Loading...")
        t = Thread(target=self._random)
        t.start()

    @updateUI
    def _show_summary(self):
        game_id = self.textbox.text()
        try:
            self.gamedata = get_game(game_id)
            if all(b.complete for b in self.gamedata.rounds):
                self.summary_label.setText(self.gamedata.date + "\n" + self.gamedata.comments)
                self.valid_game = True
            else:
                self.summary_label.setText("Game has blank questions")
                self.valid_game = False
        except ValueError as e:
            self.summary_label.setText("invalid game id")
            self.valid_game = False
        self.check_start()

    def show_summary(self, text=None):
        logging.info("show sum")
        self.summary_label.setText("Loading...")
        t = Thread(target=self._show_summary)
        t.start()

    def check_second_monitor(self):
        if len(QApplication.instance().screens()) > 1 or DEBUG:
            logging.info("hide monitor error")
            self.monitor_error.hide()
            self.windowHandle().setScreen(QApplication.instance().screens()[0])
            self.show_overlay()

        self.check_start()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        qtRectangle = self.frameGeometry()
        centerPoint = QGuiApplication.screens()[0].geometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        icon_size = 64

        icon = QPixmap(resource_path("icon.png"))
        self.icon_label.setPixmap(
            icon.scaled(
                icon_size,
                icon_size,
                transformMode=Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.icon_label.setGeometry(
            (self.rect().width() - icon_size) / 2, 10, icon_size, icon_size
        )
        self.monitor_error.setStyleSheet("QLabel { color: red}")
        self.monitor_error.setGeometry(140, 75, self.rect().width(), 20)

        QApplication.instance().screenAdded.connect(self.check_second_monitor)
        QApplication.instance().screenRemoved.connect(self.check_second_monitor)
        self.check_second_monitor()

        self.startButton.setToolTip("Start Game")
        self.startButton.move(290, 95)
        self.startButton.clicked.connect(self.init_game)

        self.randButton.setToolTip("Random Game")
        self.randButton.move(290, 120)
        # self.randButton.setFocus(False)
        self.randButton.clicked.connect(self.random)
        summary_margin = 50
        self.summary_label.setGeometry(
            summary_margin, 150, self.rect().width() - 2 * summary_margin, 40
        )
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.help_checkbox.setGeometry(
            self.summary_label.geometry().translated(165, 42)
        )

        # adds a checkbox labeled "team mode" above the "show help" checkbox
        # self.team_checkbox = QCheckBox("Team Mode", self)


        self.gameid_label.setGeometry(0, 97, 172, 50)
        self.custom_label.setGeometry(0, 127, 172, 50)
        self.textbox.move(180, 100)
        self.textbox.resize(100, 40)
        self.textbox.textChanged.connect(self.show_summary)
        f = self.textbox.font()
        f.setPointSize(30)  # sets the size to 27
        self.textbox.setFont(f)

        self.player_view = PlayerView(self.rect() - QMargins(0, 230, 0, 0), parent=self)

        if DEBUG:
            self.textbox.setText(str(2534))  # EDIT

        self.show()
        logging.info(f"Number of screens: {len(QApplication.instance().screens())}")

        ### FOR TESTING

        # self.socket_controller.connected_players = [
        # Player("Stuart", None),
        # ]
        # self.socket_controller.connected_players[0].token = bytes.fromhex(
        # "6ab3a010ce36cc5c62e3e8f219c9be"
        # )
        # self.init_game()

    def check_start(self):
        if self.startable():
            self.startButton.setEnabled(True)
        else:
            self.startButton.setEnabled(False)

    def startable(self):
        if DEBUG:
            return True
        return (
            self.valid_game
            and len(self.socket_controller.connected_players) > 0
            and len(QApplication.instance().screens()) > 1
        )

    def init_game(self):
        try:
            game_id = self.textbox.text()
            if type(game_id) == str:
                get_game(game_id)

        except ValueError as e:
            error_dialog = QErrorMessage()
            error_dialog.showMessage("Invalid game ID - change sharing permissions & try again")
            return False

        self.gamedata = get_game(game_id)
        game = Game(self.gamedata)
        game.welcome_window = self
        game.players = self.socket_controller.connected_players
        if DEBUG:
            game.players = [
                Player(f"Stuart", None),
                Player(f"Maddie", None),
                Player(f"Koda", None)
            ]

        self.run_game(game)

    def run_game(self, game):
        if self.song_player:
            self.song_player.stop()
        self.socket_controller.game = game
        game.buzzer_controller = self.socket_controller

        
        if not DEBUG:
            self.host_overlay.close()
        self.show_board(game)

    def show_board(self, game):
        game.alex_window = DisplayWindow(alex=True, monitor=0)
        game.main_window = DisplayWindow(alex=False, monitor=1)
        game.dc += game.alex_window
        game.dc += game.main_window

        self.startButton.setEnabled(False)
        if self.help_checkbox.isChecked():
            QTimer.singleShot(200, self.game.show_help)

    def restart(self):
        self.player_view.close()
        self.player_view = PlayerView(self.rect() - QMargins(0, 210, 0, 0), parent=self)
        # self.show_overlay()
        QTimer.singleShot(500, self.show_overlay)

        self.startButton.setEnabled(False)

    @updateUI
    def new_player(self, player):
        PlayerView.new_player(player)
        self.check_start()
        # label = self.player_labels[len(self.socket_controller.connected_players) - 1]
        # label.setText(player.name)
        # label.setFixedWidth(LABELWIDTH)
        # label.move(label.pos() + QPoint((MOVIEWIDTH - LABELWIDTH)/2,0))
        # label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.check_start()

    @updateUI
    def buzz_hint(self, i_player):
        player = self.socket_controller.connected_players[i_player]
        PlayerView.buzz_hint(player)
        # for l in self.player_labels:
        # if player.name == l.text():
        # l.setStyleSheet("QLabel { background-color : grey}")
        # def return_to_default(label=l, widget=self):
        # l.setStyleSheet("QLabel { background-color : none}")
        # self.update()

        # t = threading.Timer(0.1, return_to_default)
        # t.start()

        # break

    def closeEvent(self, event):
        if os.path.exists(".bkup"):
            os.remove(".bkup")
        QApplication.quit()


class PlayerLabel(QLabel):
    loading_movie = None

    def __init__(self, fontsize, parent=None):
        super().__init__(parent)
        self.fontsize = fontsize

        cls = type(self)
        if not cls.loading_movie:
            cls.loading_movie = QMovie(resource_path("loading.gif"))
            cls.loading_movie.setScaledSize(QSize(MOVIEWIDTH, MOVIEWIDTH))
            cls.loading_movie.start()
        # self.player_heading.setGeometry(0, 140, self.rect().width(), 50)
        # self.player_heading.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        f = self.font()
        f.setPointSize(self.fontsize)
        self.setFont(f)
        self.setAutoFillBackground(True)

        self.setMovie(cls.loading_movie)

        self.blink_timer = None

    def buzz_hint(self):
        self.setStyleSheet("QLabel { background-color : grey}")
        self.blink_timer = QTimer()
        # self.blink_timer.moveToThread(QApplication.instance().thread())
        self.blink_timer.timeout.connect(self._buzz_hint_callback)
        self.blink_timer.start(100)

    def _buzz_hint_callback(self):
        self.setStyleSheet("QLabel { background-color : none}")


class PlayerView(QWidget):
    instances = set()

    def __init__(self, rect, fontsize=LABELFONTSIZE, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setGeometry(rect)
        self.num_players = 0
        self.fontsize = fontsize

        self.labels = [PlayerLabel(self.fontsize, self) for _ in range(8)]
        for i, label in enumerate(self.labels):
            label_margin = (rect.width() - 8 * MOVIEWIDTH) // 9
            label.setGeometry(
                label_margin * (i + 1) + MOVIEWIDTH * i, 10, MOVIEWIDTH, MOVIEWIDTH
            )

        PlayerView.instances.add(self)
        self.show()

    @classmethod
    def new_player(cls, player):
        print(player.name)
        for i in cls.instances:
            i._new_player(player)

    @classmethod
    def buzz_hint(cls, player):
        for i in cls.instances:
            i._buzz_hint(player)

    @updateUI
    def _new_player(self, player):
        label = self.labels[self.num_players]
        self.num_players += 1
        label.setText(player.name)
        labelwidth = self.parent().size().width() // 8
        label.setFixedWidth(labelwidth)
        # label.move(label.pos() + QPoint((MOVIEWIDTH - labelwidth) / 2, 0))
        label.move(QPoint(labelwidth * (self.num_players - 1), 0))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    @updateUI
    def _buzz_hint(self, player):
        for l in self.labels:
            if player.name == l.text():
                # QMetaObject.invokeMethod(l, 'buzz_hint') # to run on main thread
                l.buzz_hint()
                # l.setStyleSheet("QLabel { background-color : grey}")
                # t = QTimer()
                # t.timer.timeout.connect(partial(self._buzz_hint_callback, l))
                # t.start(100)

                break

    def closeEvent(self, event):
        PlayerView.instances.remove(self)
        event.accept()


class HostOverlay(QWidget):
    def __init__(self, host):
        QMainWindow.__init__(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        if DEBUG:
            screen = QGuiApplication.screens()[0]
        else:
            screen = QGuiApplication.screens()[1]

        screen_width = screen.size().width()
        display_width = int(0.7 * screen_width)
        display_height = int(0.2 * display_width)
        font_size = int(0.06 * display_width)

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LayoutDirection.LeftToRight,
                Qt.AlignmentFlag.AlignCenter,
                QSize(display_width, display_height),
                screen.geometry(),
            )
        )

        font = QFont()
        font.setPointSize(font_size)


        url = "http://" + host

        self.label = QLabel(url, self)
        self.label.setGeometry(
            self.rect() - QMargins(0, 0, 0, self.rect().height() // 2)
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(font)

        self.qrlabel = QLabel(self)
        self.qrlabel.setPixmap(
            qrcode.make(url,
                        image_factory=Image,
                        box_size=self.label.rect().height()//30).pixmap())

        self.qrlabel.setGeometry( self.label.rect())
        self.qrlabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        #     self.label.geometry().right(),
        #     self.label.geometry().y(),
        #     self.label.geometry().height(),
        #     self.label.geometry().height()
        # ))


        self.playerview = PlayerView(
            self.rect() - QMargins(0, self.rect().height() // 2, 0, 0),
            fontsize=OVERLAYFONTSIZE,
            parent=self,
        )

        self.show()

    def closeEvent(self, event):
        self.playerview.close()
        event.accept()

    # def restart(self):
    # self.playerview.close()
    # self.playerview = PlayerView(
    # self.rect() - QMargins(0, self.rect().height() // 2, 0, 0),
    # fontsize = OVERLAYFONTSIZE,
    # parent = self
    # )


def find_gateway():
    Interfaces = netifaces.interfaces()
    for inter in Interfaces:
        if inter == "wlan0":
            temp_list = []
            Addresses = netifaces.ifaddresses(inter)
            gws = netifaces.gateways()
            temp_list = list(gws["default"][netifaces.AF_INET])
            count = 0
            for item in temp_list:
                count += 1
                if count == 1:
                    return item
                else:
                    pass


def get_logs():
    return sys.stdout.read() + "\n\n\n" + sys.stderr.read()


def get_sysinfo():
    return version



def main():

    # r = QFontDatabase.addApplicationFont("data:ITC_Korinna.ttf")
    # logging.info("Loading font: ",r)

    # ip_addr = '192.168.1.1'
    # ping_command = ['ping','-i','0.19',ip_addr]
    # ping_process = subprocess.Popen(ping_command, stdout=open(os.devnull, 'wb'))
    song_player = None
    if DEBUG:
        logging.warn("RUNNING IN DEBUG MODE")

    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # app = QApplication(sys.argv)

    # SC = BuzzerController()
    # wel = Welcome(SC)
    # # song_player = wel.song_player
    # SC.start()
    # r = app.exec()

    try:
        # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        app = QApplication(sys.argv)

        game = Game()

        socket_controller = BuzzerController(game)
        host_window = DisplayWindow(game, alex=True, monitor=0)
        main_window = DisplayWindow(game, alex=False, monitor=1)
        game.setDisplays(host_window, main_window)
        game.setSocketController(socket_controller)



        if DEBUG:
            game.players = [
                Player(f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAq4AAAH/CAYAAACWxV/JAAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAACrqADAAQAAAABAAAB/wAAAACSAwEjAABAAElEQVR4Ae3dB5wVRZ7A8SJnmCHnLFmygEpGEQOCsKgo4prOcOruGk69DYb1dt01rZ675xpWQRBERQlKMGEgiYCiknOGkZzzvXru6DD9urv6TYeqfr/3+fCZma7qqn996zH86dddVSgra8QpwQsBBBBAAAEEEEAAAc0FCmseH+EhgAACCCCAAAIIIJAUIHHljYAAAggggAACCCBghACJqxHTRJAIIIAAAggggAACJK68BxBAAAEEEEAAAQSMECBxNWKaCBIBBBBAAAEEEECAxJX3AAIIIIAAAggggIARAiSuRkwTQSKAAAIIIIAAAgiQuPIeQAABBBBAAAEEEDBCgMTViGkiSAQQQAABBBBAAAESV94DCCCAAAIIIIAAAkYIkLgaMU0EiQACCCCAAAIIIEDiynsAAQQQQAABBBBAwAgBElcjpokgEUAAAQQQQAABBEhceQ8ggAACCCCAAAIIGCFA4mrENBEkAggggAACCCCAAIkr7wEEEEAAAQQQQAABIwRIXI2YJoJEAAEEEEAAAQQQIHHlPYAAAggggAACCCBghACJqxHTRJAIIIAAAggggAACJK68BxBAAAEEEEAAAQSMECBxNWKaCBIBBBBAAAEEEECAxJX3AAIIIIAAAggggIARAiSuRkwTQSKAAAIIIIAAAgiQuPIeQAABBBBAAAEEEDBCgMTViGkiSAQQQAABBBBAAAESV94DCCCAAAIIIIAAAkYIkLgaMU0EiQACCCCAAAIIIEDiynsAAQQQQAABBBBAwAgBElcjpokgEUAAAQQQQAABBEhceQ8ggAACCCCAAAIIGCFA4mrENBEkAggggAACCCCAAIkr7wEEEEAAAQQQQAABIwRIXI2YJoJEAAEEEEAAAQQQIHHlPYAAAggggAACCCBghACJqxHTRJAIIIAAAggggAACJK68BxBAAAEEEEAAAQSMECBxNWKaCBIBBBBAAAEEEECAxJX3AAIIIIAAAggggIARAiSuRkwTQSKAAAIIIIAAAgiQuPIeQAABBBBA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",
                None),
                Player(f"Maddie", None),
                Player(f"Koda", None)
            ]
            game.dc.scoreboard.refresh_players()


        # song_player = wel.song_player
        try:
            socket_controller.start()
        except PermissionError as e:
            permission_error()
            raise e

        r = app.exec()

    finally:
        logging.info("terminated")
        if song_player:
            song_player.stop()
        if not DEBUG:
            try:
                sys.exit(r)
            except NameError:
                sys.exit(1)
