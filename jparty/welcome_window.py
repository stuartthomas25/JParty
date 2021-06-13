import sys
import os
from random import shuffle
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QMovie, QPixmap, QPalette, QGuiApplication, QFontDatabase, QColor
# from PyQt6.QtMultimedia import QSound
from PyQt6.QtWidgets import *  # QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt6.QtCore import Qt, QRectF, QPoint, QTimer, QSize, QDir
import logging
import pickle
from threading import Thread, active_count
from random import choice
import time
import subprocess

import threading

# from .data_rc import *
from .retrieve import get_game, get_all_games, get_game_sum
from .controller import BuzzerController
from .boardwindow import DisplayWindow
from .game import Player
from .constants import DEBUG
from .utils import SongPlayer

def updateUI(f):
    def wrapper(self, *args):
        ret = f(self, *args)
        self.update()
        return ret

    return wrapper

MOVIEWIDTH = 64
LABELWIDTH = 150

# def list_files(startpath='.'):
# for root, dirs, files in os.walk(startpath):
# level = root.replace(startpath, '').count(os.sep)
# indent = ' ' * 4 * (level)
# print('{}{}/'.format(indent, os.path.basename(root)))
# subindent = ' ' * 4 * (level + 1)
# for f in files:
# print('{}{}'.format(subindent, f))

class Welcome(QMainWindow):
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
        # final_song = QSound("data/song.mp3")
        # self.song = QSound('data:song.wav')
        self.song_player = SongPlayer()


        # print(final_song.fileName())
        # final_song.play()
        # print("play")


        # self.song.setLoops(QSound.Infinite)
        # self.song.play()
        self.song_player.play(repeat=True)

        self.icon_label = QLabel(self)
        self.startButton = QPushButton("Start!", self)

        self.randButton = QPushButton("Random", self)
        self.summary_label = QLabel("", self)
        self.summary_label.setWordWrap(True)

        self.textbox = QLineEdit(self)
        self.gameid_label = QLabel("Game ID:", self)
        # self.player_heading = QLabel("Players:", self)
        self.player_labels = [QLabel(self) for _ in range(3)]

        self.monitor_error = QLabel("JParty requires two seperate monitors", self)

        self.show()
        self.initUI()

        if os.path.exists(".bkup"):
            print('backup')
            self.run_game(pickle.load(open(".bkup", "rb")))
        else:
            self.full_index_thread = Thread(target=self.full_index)
            self.full_index_thread.start()

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
        t = Thread(target=self._show_summary)
        t.start()

    def check_second_monitor(self):
        if len(QApplication.instance().screens()) > 1:
            print("hide monitor error")
            self.monitor_error.hide()
            self.windowHandle().setScreen(QApplication.instance().screens()[0])

            self.host_overlay = HostOverlay(self.socket_controller.host())
            self.host_overlay.windowHandle().setScreen(QApplication.instance().screens()[1])
            print(QApplication.instance().screens()[0].size().width())
            print(QApplication.instance().screens()[1].size().width())
            self.host_overlay.show()

        self.check_start()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        qtRectangle = self.frameGeometry()
        centerPoint = QGuiApplication.screens()[0].geometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        icon_size = 64

        icon = QPixmap("data:icon.png")
        self.icon_label.setPixmap(
            icon.scaled(icon_size, icon_size, transformMode=Qt.TransformationMode.SmoothTransformation)
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

        loading_movie = QMovie("data:loading.gif")
        loading_movie.setScaledSize(QSize(MOVIEWIDTH, MOVIEWIDTH))
        label_fontsize = 15
        # self.player_heading.setGeometry(0, 140, self.rect().width(), 50)
        # self.player_heading.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        for i, label in enumerate(self.player_labels):
            f = label.font()
            f.setPointSize(label_fontsize)  # sets the size to 27
            label.setFont(f)
            label.setAutoFillBackground(True)

            label.setMovie(loading_movie)
            label_margin = (self.rect().width() - 3 * MOVIEWIDTH) // 4
            label.setGeometry(
                label_margin * (i + 1) + MOVIEWIDTH * i, 210, MOVIEWIDTH, MOVIEWIDTH
            )
        loading_movie.start()

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
        self.game.players = self.socket_controller.connected_players
        self.run_game(self.game)

    def run_game(self, game):
        # self.song.stop()
        self.song_player.stop()
        self.socket_controller.game = game
        game.buzzer_controller = self.socket_controller
        self.host_overlay.hide()
        self.show_board(game)

    def show_board(self, game):
        self.game.alex_window = DisplayWindow(game, alex=True, monitor=0)
        self.game.main_window = DisplayWindow(game, alex=False, monitor=1)


    @updateUI
    def new_player(self, player):
        label = self.player_labels[len(self.socket_controller.connected_players) - 1]
        label.setText(player.name)
        label.setFixedWidth(LABELWIDTH)
        label.move(label.pos() + QPoint((MOVIEWIDTH - LABELWIDTH)/2,0))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.check_start()

    @updateUI
    def buzz_hint(self, player):
        for l in self.player_labels:
            if player.name == l.text():

                l.setStyleSheet("QLabel { background-color : grey}")

                def return_to_default(label=l, widget=self):
                    l.setStyleSheet("QLabel { background-color : none}")
                    self.update()

                t = threading.Timer(0.1, return_to_default)
                t.start()

                break

    def closeEvent(self, event):
        if os.path.exists(".bkup"):
            os.remove(".bkup")
        QApplication.quit()


class HostOverlay(QMainWindow):
    def __init__(self, host):
        QMainWindow.__init__(self)
        screen = QGuiApplication.screens()[1]

        screen_width = screen.size().width()
        display_width = int(0.7 * screen_width)
        display_height = int(0.1 * display_width)
        font_size = int(0.6 * display_height)

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
        self.label.setGeometry(self.rect())
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(font)

        self.show()

def find_gateway():
      Interfaces= netifaces.interfaces()
      for inter in Interfaces:
           if inter == "wlan0":
                temp_list = []
                Addresses = netifaces.ifaddresses(inter)
                gws = netifaces.gateways()
                temp_list = list (gws['default'][netifaces.AF_INET])
                count =0
                for item in temp_list:
                      count +=1
                      if count ==1:
                           return item
                      else:
                           pass

def main():
    # game_id = 4727

    # game = get_game(game_id)
    # for r in game.rounds:
    # 	for q in r.questions:
    # 		print(q.answer)

    QDir.addSearchPath('data', 'data/')
    app = QApplication(sys.argv)
    # r = QFontDatabase.addApplicationFont("data:ITC_Korinna.ttf")
    # print("Loading font: ",r)

    SC = BuzzerController()
    wel = Welcome(SC)
    SC.start()
    # wel.start_game(SC)

    ip_addr = '192.168.1.254'
    ping_command = ['ping','-i','0.19',ip_addr]
    ping_process = subprocess.Popen(ping_command, stdout=open(os.devnull, 'wb'))

    try:
        r = app.exec()
    finally:
        ping_process.terminate()
        print("terminate")
        wel.song_player.stop()
        sys.exit(r)





