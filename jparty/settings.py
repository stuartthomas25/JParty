from PyQt6.QtGui import QPalette, QPainter, QBrush, QMovie
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
import logging

from jparty.welcome_widget import StartWidget
from jparty.utils import add_shadow, resource_path
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
        self.icon_label.setVisible(False)

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
        self.remove_button.clicked.connect(partial(self.game.remove_player, self.player))
        self.remove_button.clicked.connect(super().close)
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
                int(0.35 * fullrect.width()),
                int(0.4 * fullrect.height()),
                int(0.35 * fullrect.width()),
                int(0.4 * fullrect.height())
            )
        )
        self.setGeometry(fullrect - margins)

class NewPlayersPopup(QDialog):
    def __init__(self, parent=None):
        self.game = parent.game
        super().__init__(parent)
        self.setWindowTitle("Loading")
        self.setFixedSize(300, 200)

        # Create layout
        layout = QVBoxLayout()

        # Label for the message
        message_label = QLabel("Accepting new players...")
        message_label.setStyleSheet("font-size: 16px; text-align: center;")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message_label)

        # Spinning loading circle
        spinner_label = QLabel()

        spinner_label.setStyleSheet("""
            QPushButton {
                background: red;
                border: none;
            }
        """)
        spinner_movie = QMovie(resource_path("loading.gif"))
        spinner_label.setMovie(spinner_movie)
        spinner_movie.start()
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(spinner_label)

        # Cancel button
        cancel_button = QPushButton("Done")
        cancel_button.clicked.connect(self.close)
        layout.addWidget(cancel_button)

        # Set layout
        self.setLayout(layout)
        self.show()

    def close(self):
        self.game.buzzer_controller.accepting_players = False
        super().close()


class InGameSettingsDialog(SettingsDialog):
    # TODO should be able to
    # - skip rounds
    # - reopen players
    contentMargin = 0.5
    def __init__(self, parent=None):
        # self.allowing_new_players = False
        super().__init__(parent)

        layout = QVBoxLayout()
        # layout.addStretch(5)
        # layout.addLayout(self.icon_layout, 10)

        self.title_label = QLabel("Game Settings", self)
        self.title_font.setPixelSize(int(20))
        self.title_label.setFont(self.title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label, 2)



        summary_string = self.game.data.date + "\n" + self.game.data.comments
        self.summary_label = QLabel(summary_string, self)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.summary_label, 2)

        self.help_label = QLabel(modify_players_help_text, self)
        self.help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.help_label, 2)


        self.next_button = QPushButton("Next round", self)
        self.next_button.clicked.connect(self.game.next_round)
        self.next_button.clicked.connect(self.disable_buttons)
        layout.addWidget(self.next_button, 3)

        self.prev_button = QPushButton("Previous round", self)
        self.prev_button.clicked.connect(self.game.prev_round)
        self.prev_button.clicked.connect(self.disable_buttons)
        layout.addWidget(self.prev_button, 3)

        self.quit_button = QPushButton("Quit game", self)
        self.quit_button.clicked.connect(self.quit_game)
        layout.addWidget(self.quit_button, 3)

        self.open_button = QPushButton("Allow new players", self)
        self.open_button.clicked.connect(self.allow_new_players)
        layout.addWidget(self.open_button, 3)

        self.close_button = QPushButton("Done", self)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button, 3)

        m = int(PlayerSettingsDialog.contentMargin * self.width())
        layout.setContentsMargins(m,0,m,m)
        layout.setSpacing(10)

        self.setLayout(layout)
        self.disable_buttons()
        self.show()

    def quit_game(self):
        confirmation_dialog = QMessageBox(self)
        confirmation_dialog.setWindowTitle("Confirm quit")
        confirmation_dialog.setText("Are you sure you want to quit?")
        confirmation_dialog.setIcon(QMessageBox.Icon.Question)

        # Add Yes and No buttons
        confirmation_dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        # Execute and handle the response
        response = confirmation_dialog.exec()
        if response == QMessageBox.StandardButton.Yes:
            self.game.close_game()
            self.close()

    def allow_new_players(self):
        logging.info("allow new players")
        NewPlayersPopup(self)
        self.game.buzzer_controller.accepting_players = True

    def disable_buttons(self):
        i = self.game.index_of_current_round()
        self.prev_button.setDisabled(i == 0)
        self.next_button.setDisabled(i == 2)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        fullrect = self.parent().rect()
        margins = (
            QMargins(
                int(0.35 * fullrect.width()),
                int(0.25 * fullrect.height()),
                int(0.35 * fullrect.width()),
                int(0.25 * fullrect.height())
            )
        )
        self.setGeometry(fullrect - margins)
