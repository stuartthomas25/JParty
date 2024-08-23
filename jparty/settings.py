from PyQt6.QtCore import Qt
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
from jparty.utils import DynamicButton

modify_players_help_text = """
Click scores to change a player's score.
Remove players with the red x.
Players can join with link.
"""

class SettingsDialog(StartWidget):
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

        self.close_button = DynamicButton("Done", self)
        self.close_button.clicked.connect(self.close)

        # # Add OK and Cancel buttons
        # buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        # buttons.accepted.connect(self.accept)

        # layout.addWidget(buttons)

        self.setLayout(layout)

    def show(self):
        super().show()
        self.game.modify_players(True)

    def close(self):
        super().close()
        self.game.modify_players(False)
