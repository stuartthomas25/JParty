from PyQt6.QtGui import (
    QPainter,
    QBrush,
    QImage,
    QFont,
    QPalette,
    QPixmap,
    QColor, 
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QSizePolicy,
    QMessageBox,
    QLabel,
    QDialog,
    QComboBox,
    QPushButton,
    QTableWidget,
    QHeaderView,
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject

import qrcode
import time
from threading import Thread
import logging
import json
import os
import sys

from jparty.constants import DEFAULT_CONFIG
from jparty.scoreboard import NameLabel

stats_labels = [
    "Players",
    "Awards",
    "First buzzes",
    "Early buzzes",
    "Late buzzes",
    "Fastest buzz",
    "Correct",
    "Incorrect",
    "Total revenue",
    "Total losses",
]


class StatsBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Read the current theme from the configuration file
        with open('config.json', 'r') as f:
            config = json.load(f)
        current_earlybuzztimeout = config.get('earlybuzztimeout', DEFAULT_CONFIG['earlybuzztimeout'])

        self.setWindowTitle("Buzz Stats")
        self.resize(1250, 600)
        layout = QVBoxLayout()

        game = parent.game

        table = QTableWidget()
        table.setColumnCount(len(game.players)+1)
        table.setRowCount(len(stats_labels))

        font = QFont()
        font.setPointSize(16)
        table.setFont(font)

        # Set the first column to be the stats labels
        for i, label in enumerate(stats_labels):
            label_widget = QLabel(label + ":")
            font = label_widget.font()
            font.setBold(True)
            font.setPointSize(16)
            label_widget.setFont(font)
            table.setCellWidget(i, 0, label_widget)
        
        awards = {
            "Most Correct": [None, 0],
            "Most Wrong": [None, 0],
            "Most Revenue": [None, 0],
            "Quickest Buzzer": [None, 0],
            "Most buzz-ins": [None, 0],
        }

        for i, player in enumerate(game.players):
            name_label = NameLabel(player.name, self)
            table.setCellWidget(0, i+1, name_label)
            table.setCellWidget(1, i+1, QLabel(""))
            table.cellWidget(1, i+1).setWordWrap(True)
            # Allow above cell to take up more height if words wrap
            table.verticalHeader().setSectionResizeMode(i+1, QHeaderView.ResizeMode.ResizeToContents)

            # Show first, early, and late buzz stats
            first_buzzes = 0
            early_buzzes = 0
            late_buzzes = 0
            fastest_buzz = None
            for buzz in player.buzz_delays:
                if buzz["timing"] == "first":
                    first_buzzes += 1
                    if fastest_buzz is None or buzz["delay"] < fastest_buzz:
                        fastest_buzz = buzz["delay"]
                elif buzz["timing"] == "early":
                    early_buzzes += 1
                elif buzz["timing"] == "late":
                    late_buzzes += 1
            table.setCellWidget(2, i+1, QLabel(str(first_buzzes)))
            table.setCellWidget(3, i+1, QLabel(str(early_buzzes)))
            table.setCellWidget(4, i+1, QLabel(str(late_buzzes)))
            if fastest_buzz is not None:
                table.setCellWidget(5, i+1, QLabel(f"{fastest_buzz:.3f}s"))
            else:
                table.setCellWidget(5, i+1, QLabel("N/A"))
            
            # Other stats which are already prerecorded
            table.setCellWidget(6, i+1, QLabel(str(player.stats["correct"])))
            table.setCellWidget(7, i+1, QLabel(str(player.stats["incorrect"])))
            table.setCellWidget(8, i+1, QLabel(f"${player.stats['revenue']:,}"))
            table.setCellWidget(9, i+1, QLabel(f"${player.stats['losses']:,}"))

            self.update_awards(i+1, player, awards, first_buzzes, fastest_buzz)

        # Display awards
        for award in awards:
            if awards[award][0] is not None:
                # Get existing text in cell
                text = table.cellWidget(1, awards[award][0]).text()
                if text == "":
                    text = " "
                else:
                    text += ", "
                logging.info(f"col: {awards[award][0]}")
                table.cellWidget(1, awards[award][0]).setText("🏆" + text + award)

        # Set the table width to match the window width
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Set first row height to 100 pixels
        table.setRowHeight(0, 100)

        layout.addWidget(table)
        self.setLayout(layout)
    
    def update_awards(self, col, player, awards, first_buzzes, fastest_buzz):
        for award in awards:
            if award == "Most Correct":
                if player.stats["correct"] > awards[award][1]:
                    awards[award] = [col, player.stats["correct"]]
            elif award == "Most Wrong":
                if player.stats["incorrect"] > awards[award][1]:
                    awards[award] = [col, player.stats["incorrect"]]
            elif award == "Most Revenue":
                if player.stats["revenue"] > awards[award][1]:
                    awards[award] = [col, player.stats["revenue"]]
            elif award == "Quickest Buzzer":
                if fastest_buzz is not None:
                    if fastest_buzz < awards[award][1]:
                        awards[award] = [col, fastest_buzz]
            elif award == "Most buzz-ins":
                if first_buzzes > awards[award][1]:
                    awards[award] = [col, first_buzzes]