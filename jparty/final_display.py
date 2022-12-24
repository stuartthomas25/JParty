from PyQt6.QtWidgets import QWidget, QVBoxLayout

from jparty.scoreboard import NameLabel
from jparty.style import MyLabel, CARDPAL
from jparty.utils import add_shadow


class FinalDisplay(QWidget):
    def __init__(self, game, parent):
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.answer_widget = FinalAnswerWidget(game, self)
        main_layout = QVBoxLayout()
        main_layout.addStretch(4)
        main_layout.addWidget(self.answer_widget, 2)
        main_layout.addStretch(3)
        self.setLayout(main_layout)

        self.show()


class FinalAnswerWidget(QWidget):
    def __init__(self, game, parent):
        super().__init__(parent)
        self.game = game
        self.winner_label = None

        self.main_layout = QVBoxLayout()
        self.guess_label = MyLabel("", self.startFontSize, self)
        self.wager_label = MyLabel("", self.startFontSize, self)

        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.guess_label, 5)
        self.main_layout.addWidget(self.wager_label, 5)
        self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)

        self.setPalette(CARDPAL)
        self.setAutoFillBackground(True)
        add_shadow(self)

        self.show()

    def startFontSize(self):
        return self.height() * 0.2

    def show_winner(self, winner):
        self.guess_label.setText("We have a winner!")
        self.wager_label.setText("")
        self.winner_label = NameLabel(winner.name, self)
        self.main_layout.replaceWidget(self.wager_label, self.winner_label)

    def show_tie(self):
        self.guess_label.setText("We have a tie!")
        self.wager_label.setText("")
