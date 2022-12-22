import sys
import os
from PyQt6.QtGui import (
    QImage,
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFont,
    QMovie,
    QPixmap,
    QDesktopServices,
    QPalette,
    QGuiApplication,
    QFontDatabase,
    QColor,
)

import requests


# from PyQt6.QtMultimedia import QSound
from PyQt6.QtWidgets import *  # QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt6.QtCore import Qt, QRectF, QRect, QPoint, QTimer, QSize, QDir, QMargins, pyqtSignal
import logging

import pickle
from threading import Thread, active_count
import time
import subprocess

import threading
from functools import partial

# from .data_rc import *
from .retrieve import get_game, get_game_sum
from .controller import BuzzerController
from .boardwindow import DisplayWindow, HostDisplayWindow
from .game import Player, Game
from .constants import DEBUG
from .utils import SongPlayer, resource_path, check_internet
from .logger import qt_exception_hook


class JPartyStyle(QCommonStyle):
    PM_dict = {
        QStyle.PixelMetric.PM_LayoutBottomMargin : 0,
        QStyle.PixelMetric.PM_LayoutLeftMargin : 0,
        QStyle.PixelMetric.PM_LayoutRightMargin : 0,
        QStyle.PixelMetric.PM_LayoutTopMargin : 0,
        QStyle.PixelMetric.PM_LayoutHorizontalSpacing: 0,
        QStyle.PixelMetric.PM_LayoutVerticalSpacing: 0,
    }
    SH_dict = {
        QStyle.StyleHint.SH_Button_FocusPolicy: 0,
    }

    def pixelMetric(self, key, *args, **kwargs):
        return JPartyStyle.PM_dict.get(key,
                                       super().pixelMetric(key, *args, **kwargs))

    def styleHint(self, key, *args, **kwargs):
        return JPartyStyle.SH_dict.get(key,
                                       super().styleHint(key, *args, **kwargs))
