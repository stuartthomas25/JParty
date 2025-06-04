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
)

from jparty.welcome_widget import StartWidget
from jparty.utils import DynamicButton, add_shadow
from jparty.style import WINDOWPAL

modify_players_help_text = """
Click scores to change a player's score.
Remove players with the red x.
Players can join with link.
"""

class SettingsDialog(StartWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game = parent.game
        add_shadow(self, radius=0.2)
        self.setPalette(WINDOWPAL)
        # self.setWindowTitle("Settings")


        # Create layout and form elements for settings
        layout = QVBoxLayout()


        # # Add OK and Cancel buttons
        # buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        # buttons.accepted.connect(self.accept)

        # layout.addWidget(buttons)

        self.setLayout(layout)

    # def show(self):
    #     super().show()

    # def close(self):
    #     super().close()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(QBrush(WINDOWPAL.color(QPalette.ColorRole.Window)))
        qp.drawRect(self.rect())

    def resizeEvent(self, event):
        fullrect = self.parent().rect()
        margins = (
            QMargins(
                fullrect.width(), fullrect.height(), fullrect.width(), fullrect.height()
            )
            * 0.3
        )
        self.setGeometry(fullrect - margins)

class PlayerSettingsDialog(SettingsDialog):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player

        layout = QVBoxLayout()

        self.player_label = QLabel(modify_players_help_text, self)
        self.player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.player_label)


        self.remove_button = DynamicButton("Done", self)
        self.remove_button.clicked.connect(self.close)

        self.score_button = DynamicButton("Done", self)
        self.score_button.clicked.connect(self.close)

        self.close_button = DynamicButton("Done", self)
        self.close_button.clicked.connect(self.close)

        # # Add OK and Cancel buttons
        # buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        # buttons.accepted.connect(self.accept)

        # layout.addWidget(buttons)

        self.setLayout(layout)

    def show(self):
        super().show()
        # self.game.modify_players(True)
        #
    def close(self):
        super().close()
        # self.game.modify_players(False)

class InGameSettingsDialog(StartWidget):
    # TODO should be able to
    # - skip rounds
    # - reopen players

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game = parent.game
        # self.setWindowTitle("Settings")

        # Create layout and form elements for settings
        layout = QVBoxLayout()

        self.player_label = QLabel(modify_players_help_text, self)
        self.player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.username_input = QLineEdit(self)
        # self.email_input = QLineEdit(self)

        # layout.addRow("Username:", self.username_input)
        # layout.addRow("Email:", self.email_input)
        layout.addWidget(self.player_label)

        self.remove_button = DynamicButton("Done", self)
        self.remove_button.clicked.connect(self.close)

        self.score_button = DynamicButton("Done", self)
        self.score_button.clicked.connect(self.close)

        self.close_button = DynamicButton("Done", self)
        self.close_button.clicked.connect(self.close)

        # # Add OK and Cancel buttons
        # buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        # buttons.accepted.connect(self.accept)

        # layout.addWidget(buttons)

        self.setLayout(layout)
