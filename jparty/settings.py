from PyQt6.QtGui import QPalette, QPainter, QBrush
from PyQt6.QtCore import Qt, QMargins
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QFormLayout,
    QVBoxLayout,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
    QComboBox,
    QPushButton
)

from functools import partial

from jparty.welcome_widget import StartWidget
from jparty.utils import add_shadow
from jparty.style import WINDOWPAL

modify_players_help_text = """
Click on a player's podium for player settings
"""

class SettingsDialog(StartWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game = parent.game
        add_shadow(self, radius=0.2)
        self.setPalette(WINDOWPAL)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(QBrush(WINDOWPAL.color(QPalette.ColorRole.Window)))
        qp.drawRect(self.rect())

class PlayerSettingsDialog(SettingsDialog):
    contentMargin = 0.5
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player

        layout = QVBoxLayout()
        layout.addLayout(self.icon_layout, 1)

        self.title_label = QLabel("Player Settings", self)
        self.title_font.setPixelSize(int(20))
        self.title_label.setFont(self.title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label, 4)


        self.remove_button = QPushButton("Remove player", self)
        self.remove_button.clicked.connect(self.remove_player)
        layout.addWidget(self.remove_button, 3)

        self.score_button = QPushButton("Change score", self)
        self.score_button.clicked.connect(partial(self.game.adjust_score,self.player))
        layout.addWidget(self.score_button, 3)

        self.close_button = QPushButton("Done", self)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button, 3)


        m = int(PlayerSettingsDialog.contentMargin * self.width())
        layout.setContentsMargins(m,0,m,m)
        layout.setSpacing(10)

        self.setLayout(layout)

    def remove_player(self):
        self.game.remove_player(self.player)
        super().close()

    def close(self):
        pwidget = self.parent().player_widget(self.player)
        if pwidget is not None:
            pwidget.set_lights(False)
        super().close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        fullrect = self.parent().rect()
        margins = (
            QMargins(
                0.35 * fullrect.width(), 0.4 * fullrect.height(), 0.35 * fullrect.width(), 0.4 * fullrect.height()
            )
        )
        self.setGeometry(fullrect - margins)


class InGameSettingsDialog(SettingsDialog):
    # TODO should be able to
    # - skip rounds
    # - reopen players
    contentMargin = 0.5
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.addStretch(5)
        layout.addLayout(self.icon_layout, 10)

        self.title_label = QLabel("Game Settings", self)
        self.title_font.setPixelSize(int(20))
        self.title_label.setFont(self.title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label, 3)

        self.help_label = QLabel(modify_players_help_text, self)
        self.help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.help_label, 4)

        self.next_button = QPushButton("Next round", self)
        # self.next_button.clicked.connect(self.game.__) # TODO
        layout.addWidget(self.next_button, 3)

        self.quit_button = QPushButton("Quit game", self)
        # self.quit_button.clicked.connect(partial(self.game.adjust_score,self.player))
        layout.addWidget(self.quit_button, 3)

        self.open_button = QPushButton("Allow new players", self)
        # self.open_button.clicked.connect(partial(self.game.adjust_score,self.player))
        layout.addWidget(self.open_button, 3)

        self.close_button = QPushButton("Done", self)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button, 3)

        m = int(PlayerSettingsDialog.contentMargin * self.width())
        layout.setContentsMargins(m,0,m,m)
        layout.setSpacing(10)

        self.setLayout(layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        fullrect = self.parent().rect()
        margins = (
            QMargins(
                0.3 * fullrect.width(), 0.3 * fullrect.height(), 0.3 * fullrect.width(), 0.3 * fullrect.height()
            )
        )
        self.setGeometry(fullrect - margins)
