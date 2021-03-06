import sys
import os
from random import shuffle
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFont,
    QMovie,
    QPixmap,
    QPalette,
    QGuiApplication,
    QFontDatabase,
    QColor,
)

# from PyQt6.QtMultimedia import QSound
from PyQt6.QtWidgets import *  # QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt6.QtCore import Qt, QRectF, QPoint, QTimer, QSize, QDir, QMargins, pyqtSignal
import logging
import pickle
from threading import Thread, active_count
from random import choice
import time
import subprocess

import threading
from functools import partial

# from .data_rc import *
from .retrieve import get_game, get_all_games, get_game_sum
from .controller import BuzzerController
from .boardwindow import DisplayWindow
from .game import Player
from .constants import DEBUG
from .utils import SongPlayer, resource_path


def updateUI(f):
    def wrapper(self, *args):
        ret = f(self, *args)
        self.update()
        return ret

    return wrapper


MOVIEWIDTH = 64
LABELFONTSIZE = 15
OVERLAYFONTSIZE = 40


class Welcome(QMainWindow):
    buzz_hint_trigger = pyqtSignal(int)

    def __init__(self, SC):
        super().__init__()
        self.socket_controller = SC
        self.socket_controller.welcome_window = self
        self.title = "JParty!"
        self.left = 10
        self.top = 10
        self.width = 500
        self.height = 300
        self.all_games = None
        self.valid_game = False
        self.game = None
        self.song_player = SongPlayer()
        self.host_overlay = None

        self.buzz_hint_trigger.connect(self.buzz_hint)

        # print(final_song.fileName())
        # final_song.play()
        # print("play")

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

        self.textbox = QLineEdit(self)
        self.gameid_label = QLabel("Game ID:", self)
        # self.player_heading = QLabel("Players:", self)
        # self.player_labels = [QLabel(self) for _ in range(3)]

        self.monitor_error = QLabel("JParty requires two seperate monitors", self)

        self.show()
        self.initUI()

        if os.path.exists(".bkup"):
            print("backup")
            self.run_game(pickle.load(open(".bkup", "rb")))
        else:
            self.full_index_thread = Thread(target=self.full_index)
            self.full_index_thread.start()

    def show_overlay(self):
        self.host_overlay = HostOverlay(self.socket_controller.host())
        self.windowHandle().setScreen(
            QApplication.instance().screens()[1]
        )
        self.host_overlay.showNormal()


    def full_index(self):
        self.all_games = []
        if not DEBUG:
            self.all_games = get_all_games()

        print("got all games")

    @updateUI
    def random(self, checked):
        self.full_index_thread.join()
        game_id = choice(self.all_games)
        # self.game = get_game(game_id)
        # while not self.game.complete():
        #    self.game = get_game(game_id)

        self.textbox.setText(str(game_id))
        self.textbox.show()

    @updateUI
    def _show_summary(self):
        game_id = self.textbox.text()
        try:
            self.game = get_game(game_id)
            if self.game.complete():
                self.summary_label.setText(self.game.date + "\n" + self.game.comments)
                self.valid_game = True
            else:
                self.summary_label.setText("Game has blank questions")
                self.valid_game = False
        except ValueError as e:
            self.summary_label.setText("invalid game id")
            self.valid_game = False
        self.check_start()

    def show_summary(self, text=None):
        print("show sum")
        self.summary_label.setText("Loading...")
        t = Thread(target=self._show_summary)
        t.start()

    def check_second_monitor(self):
        if len(QApplication.instance().screens()) > 1:
            print("hide monitor error")
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
        self.startButton.move(280, 95)
        self.startButton.clicked.connect(self.init_game)
        self.startButton.setEnabled(False)

        self.randButton.setToolTip("Random Game")
        self.randButton.move(280, 120)
        # self.randButton.setFocus(False)
        self.randButton.clicked.connect(self.random)
        summary_margin = 50
        self.summary_label.setGeometry(
            summary_margin, 150, self.rect().width() - 2 * summary_margin, 40
        )
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.gameid_label.move(120, 105)
        self.textbox.move(180, 100)
        self.textbox.resize(100, 40)
        self.textbox.textChanged.connect(self.show_summary)
        f = self.textbox.font()
        f.setPointSize(30)  # sets the size to 27
        self.textbox.setFont(f)

        self.player_view = PlayerView(self.rect() - QMargins(0, 210, 0, 0), parent=self)

        if DEBUG:
            self.textbox.setText(str(2534))  # EDIT

        self.show()
        print("Number of screens:", len(QApplication.instance().screens()))

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
        return (
            self.valid_game
            and len(self.socket_controller.connected_players) > 0
            and len(QApplication.instance().screens()) > 1
        )

    def init_game(self):
        try:
            game_id = int(self.textbox.text())
        except ValueError as e:
            error_dialog = QErrorMessage()
            error_dialog.showMessage("Invalid game ID")
            return False

        self.game = get_game(game_id)
        self.game.welcome_window = self
        self.game.players = self.socket_controller.connected_players
        self.run_game(self.game)

    def run_game(self, game):
        if self.song_player:
            self.song_player.stop()
        self.socket_controller.game = game
        game.buzzer_controller = self.socket_controller
        self.host_overlay.close()
        self.show_board(game)

    def show_board(self, game):
        self.game.alex_window = DisplayWindow(game, alex=True, monitor=0)
        self.game.main_window = DisplayWindow(game, alex=False, monitor=1)

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

        self.labels = [PlayerLabel(self.fontsize, self) for _ in range(3)]
        for i, label in enumerate(self.labels):
            label_margin = (rect.width() - 3 * MOVIEWIDTH) // 4
            label.setGeometry(
                label_margin * (i + 1) + MOVIEWIDTH * i, 10, MOVIEWIDTH, MOVIEWIDTH
            )

        PlayerView.instances.add(self)
        self.show()

    @classmethod
    def new_player(cls, player):
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
        labelwidth = self.parent().size().width() // 3
        label.setFixedWidth(labelwidth)
        # label.move(label.pos() + QPoint((MOVIEWIDTH - labelwidth) / 2, 0))
        label.move(QPoint(labelwidth*(self.num_players-1), 0))
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
        self.label = QLabel("http://" + host, self)
        self.label.setGeometry(
            self.rect() - QMargins(0, 0, 0, self.rect().height() // 2)
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(font)

        self.playerview = PlayerView(
            self.rect() - QMargins(0, self.rect().height() // 2, 0, 0),
            fontsize = OVERLAYFONTSIZE,
            parent = self
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


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    # r = QFontDatabase.addApplicationFont("data:ITC_Korinna.ttf")
    # print("Loading font: ",r)
    SC = BuzzerController()
    wel = Welcome(SC)
    SC.start()

    # ip_addr = '192.168.1.1'
    # ping_command = ['ping','-i','0.19',ip_addr]
    # ping_process = subprocess.Popen(ping_command, stdout=open(os.devnull, 'wb'))

    try:
        r = app.exec()
    finally:
        print("terminate")
        if wel.song_player:
            wel.song_player.stop()
        sys.exit(r)
