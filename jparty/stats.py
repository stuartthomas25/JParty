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
    "First buzzes",
    "Early buzzes",
    "Late buzzes",
    "Average buzz time",
    "Fastest buzz",
]


class StatsBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Read the current theme from the configuration file
        with open('config.json', 'r') as f:
            config = json.load(f)
        current_earlybuzztimeout = config.get('earlybuzztimeout', DEFAULT_CONFIG['earlybuzztimeout'])

        self.setWindowTitle("Buzz Stats")
        self.resize(1400, 600)
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

        for i, player in enumerate(game.players):
            name_label = NameLabel(player.name, self)
            table.setCellWidget(0, i+1, name_label)

            # Show first, early, and late buzz stats
            first_buzzes = 0
            early_buzzes = 0
            late_buzzes = 0
            average_buzz = None
            fastest_buzz = None
            for buzz in player.buzz_delays:
                if average_buzz is None:
                    average_buzz = 0
                if buzz["timing"] == "first":
                    first_buzzes += 1
                    average_buzz += buzz["delay"]
                    if fastest_buzz is None or buzz["delay"] < fastest_buzz:
                        fastest_buzz = buzz["delay"]
                elif buzz["timing"] == "early":
                    early_buzzes += 1
                    average_buzz -= buzz["delay"]
                elif buzz["timing"] == "late":
                    late_buzzes += 1
                    average_buzz += buzz["delay"]
            if average_buzz is not None:
                average_buzz /= len(player.buzz_delays)
            table.setCellWidget(1, i+1, QLabel(str(first_buzzes)))
            table.setCellWidget(2, i+1, QLabel(str(early_buzzes)))
            table.setCellWidget(3, i+1, QLabel(str(late_buzzes)))
            if average_buzz is not None:
                if average_buzz < 0:
                    average_buzz_label = QLabel(f"{abs(average_buzz):.3f}s early")
                else:
                    average_buzz_label = QLabel(f"{average_buzz:.3f}s")
            else:
                average_buzz_label = QLabel("N/A")
            table.setCellWidget(4, i+1, average_buzz_label)
            if fastest_buzz is not None:
                table.setCellWidget(5, i+1, QLabel(f"{fastest_buzz:.3f}s"))
            else:
                table.setCellWidget(5, i+1, QLabel("N/A"))


        # Set the table width to match the window width
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Set first row height to 100 pixels
        table.setRowHeight(0, 100)

        layout.addWidget(table)
        self.setLayout(layout)