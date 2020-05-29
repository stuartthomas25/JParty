import sys
import os
from random import shuffle
from PyQt5.QtGui import QPainter, QPen, QBrush, QImage, QColor, QFont
from PyQt5.QtWidgets import *#QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt5.QtCore import Qt, QRectF, QPoint, QTimer, QSize
import logging
import pickle

from .retrieve import get_game
from .buzzer.controller import BuzzerController
from .boardwindow import DisplayWindow

class Welcome(QMainWindow):
    def __init__(self, SC):
        super().__init__()
        self.socket_controller = SC
        self.socket_controller.welcome_window = self
        self.title = 'JParty!'
        self.left = 10
        self.top = 10
        self.width = 500
        self.height = 300

        self.startButton = QPushButton('Start!', self)

        self.randButton = QPushButton('Random', self)

        self.textbox = QLineEdit(self)
        self.gameid_label = QLabel("Game ID:", self)
        self.player_heading = QLabel("Players:", self)
        self.player_labels = [QLabel("<i>Waiting...</i>", self) for _ in range(3)]
        self.players = []

        self.monitor_error = QLabel("JParty requires two seperate monitors", self)


        self.show()
        self.initUI()

        if os.path.exists(".bkup"):
            self.run_game(pickle.load(open(".bkup",'rb')))

    def check_second_monitor(self):
        if len(qApp.screens()) > 1:
            self.monitor_error.hide()
            self.windowHandle().setScreen(qApp.screens()[0])

            self.host_overlay = HostOverlay(self.socket_controller.host())
            self.host_overlay.windowHandle().setScreen(qApp.screens()[1])
            self.host_overlay.show()

    def initUI(self):
        print(self.socket_controller.localip())
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self.monitor_error.setStyleSheet("QLabel { color: red}")
        self.monitor_error.setGeometry(140, 30, self.rect().width(), 50)

        qApp.screenAdded.connect(self.check_second_monitor)
        self.check_second_monitor()


        self.startButton.setToolTip('Start Game')
        self.startButton.move(280,95)
        self.startButton.clicked.connect(self.start_game)
        self.startButton.setEnabled(False)

        self.randButton.setToolTip('Random Game')
        self.randButton.move(280,120)
        self.randButton.setFocus(False)

        self.gameid_label.move(120,105)
        self.textbox.move(180, 100)
        self.textbox.resize(100,40)

        self.player_heading.setGeometry(120, 150, 100, 50)
        for i,label in enumerate(self.player_labels):
            label_width = 20
            label.setGeometry(150, 190+label_width*i, 100, label_width)

        self.show()
        print(len(qApp.screens()))

    def activate_start(self):
        self.startButton.setEnabled(True)


    def start_game(self):
        try:
            game_id = int(self.textbox.text())
        except ValueError as e:
            error_dialog = QErrorMessage()
            error_dialog.showMessage('Invalid game ID')
            return False

        game = get_game(game_id)

        game.scores = {n:0 for n in self.players}
        self.run_game(game)

    def run_game(self, game):
        print(game.rounds)
        self.socket_controller.game = game
        game.buzzer_controller = self.socket_controller
        self.host_overlay.hide()
        self.show_board(game)


    def show_board(self, game):
        self.alex_window = DisplayWindow(game,alex=True,monitor=0)
        self.main_window = DisplayWindow(game,alex=False,monitor=1)

    def new_player(self, name):
        self.player_labels[len(self.players)].setText(name)
        self.players.append(name)
        self.activate_start()
        self.update()

    def closeEvent(self, event):
        if os.path.exists(".bkup"):
            os.remove('.bkup')
        QApplication.quit()


class HostOverlay(QMainWindow):
    def __init__(self, host):
        QMainWindow.__init__(self)

        screen_width = QDesktopWidget().screenGeometry(1).width()
        display_width = int(0.7 * screen_width)
        display_height = int(0.1 * display_width)
        font_size = int(0.6 * display_height)

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.X11BypassWindowManagerHint
            )
        self.setGeometry(QStyle.alignedRect(
            Qt.LeftToRight, Qt.AlignCenter,
            QSize(display_width, display_height),
            QDesktopWidget().screenGeometry(1)))

        font = QFont()
        font.setPointSize(font_size)
        self.label = QLabel("http://"+host, self)
        self.label.setGeometry(self.rect())
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.label.setFont(font)


        self.show()


def main():
    # game_id = 4727

    # game = get_game(game_id)
    # for r in game.rounds:
    # 	for q in r.questions:
    # 		print(q.answer)

    app = QApplication(sys.argv)
    SC = BuzzerController()
    wel = Welcome(SC)
    SC.start()
    #wel.start_game(SC)

    sys.exit(app.exec_())
