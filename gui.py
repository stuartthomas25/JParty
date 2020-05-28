import sys
from random import shuffle
from PyQt5.QtGui import QPainter, QPen, QBrush, QImage, QColor
from PyQt5.QtWidgets import *#QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt5.QtCore import Qt, QRectF, QPoint, QTimer

from retrieve import get_game
from buzzer.controller import BuzzerController
from boardwindow import DisplayWindow

class Welcome(QMainWindow):
    def __init__(self, SC):
        super().__init__()
        self.socket_controller = SC
        self.socket_controller.welcome_window = self
        self.title = 'Jeopardy!'
        self.left = 10
        self.top = 10
        self.width = 500
        self.height = 300

        self.alex_window = None
        self.startButton = QPushButton('Start!', self)
        self.textbox = QLineEdit(self)
        self.host = QLabel("Join at http://"+self.socket_controller.host(), self)
        self.player_heading = QLabel("Players:", self)
        self.player_labels = [QLabel("<i>Waiting...</i>", self) for _ in range(3)]
        self.players = []

        self.initUI()

    def initUI(self):
        print(self.socket_controller.localip())
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())


        self.startButton.setToolTip('Start Game')
        self.startButton.move(280,100)
        self.startButton.clicked.connect(self.start_game)

        self.textbox.move(180, 100)
        self.textbox.resize(100,40)
        self.textbox.setText("4727")

        self.host.setGeometry(150, 10, 400, 50)

        self.player_heading.setGeometry(150, 150, 100, 50)
        for i,label in enumerate(self.player_labels):
            label_width = 20
            label.setGeometry(180, 190+label_width*i, 100, label_width)

        self.show()


    def start_game(self):
        try:
            game_id = int(self.textbox.text())
        except ValueError as e:
            error_dialog = QErrorMessage()
            error_dialog.showMessage('Invalid game ID')
            return False

        game = get_game(game_id)
        game.scores = {n:0 for n in self.players}
        self.socket_controller.game = game
        game.buzzer_controller = self.socket_controller
        self.show_board(game)

    def show_board(self, game):
        self.alex_window = DisplayWindow(game,alex=True,monitor=0)
        self.main_window = DisplayWindow(game,alex=False,monitor=1)
        self.hide()

    def new_player(self, name):
        self.player_labels[len(self.players)].setText(name)
        self.players.append(name)
        self.update()

if __name__ == '__main__':

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
