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
from .boardwindow import DisplayWindow
from .game import Player, Game
from .constants import DEBUG
from .utils import SongPlayer, resource_path
from .logger import qt_exception_hook


def updateUI(f):
    def wrapper(self, *args):
        ret = f(self, *args)
        self.update()
        return ret

    return wrapper


MOVIEWIDTH = 64
LABELFONTSIZE = 15
OVERLAYFONTSIZE = 40

    # def restart(self):
    # self.playerview.close()
    # self.playerview = PlayerView(
    # self.rect() - QMargins(0, self.rect().height() // 2, 0, 0),
    # fontsize = OVERLAYFONTSIZE,
    # parent = self
    # )


def find_gateway():
    Interfaces = netifaces.interfaces()
    for inter in Interfaces:
        if inter == "wlan0":
            temp_list = []
            Addresses = netifaces.ifaddresses(inter)
            gws = netifaces.gateways()
            temp_list = list(gws["default"][netifaces.AF_INET])
            count = 0
            for item in temp_list:
                count += 1
                if count == 1:
                    return item
                else:
                    pass

def get_logs():
    return sys.stdout.read() + "\n\n\n" + sys.stderr.read()


def get_sysinfo():
    return version

def check_second_monitor():
    if len(QApplication.instance().screens()) < 2 and not DEBUG:
        print("error!")
        msgBox = QMessageBox()
        msgBox.setText("JParty needs two separate displays. Please attach a second monitor or turn off mirroring and try again.")
        msgBox.exec()
        sys.exit(1)


def main():

    # r = QFontDatabase.addApplicationFont("data:ITC_Korinna.ttf")
    # logging.info("Loading font: ",r)

    # ip_addr = '192.168.1.1'
    # ping_command = ['ping','-i','0.19',ip_addr]
    # ping_process = subprocess.Popen(ping_command, stdout=open(os.devnull, 'wb'))
    song_player = None
    if DEBUG:
        logging.warn("RUNNING IN DEBUG MODE")

    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # app = QApplication(sys.argv)

    # SC = BuzzerController()
    # wel = Welcome(SC)
    # # song_player = wel.song_player
    # SC.start()
    # r = app.exec()

    app = QApplication(sys.argv)
    # check_second_monitor()
    app.setFont(QFont("Verdana"))

    # try:
        # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    game = Game()

    socket_controller = BuzzerController(game)
    game.setSocketController(socket_controller)

    host_window = DisplayWindow(game, alex=True, monitor=0)
    main_window = DisplayWindow(game, alex=False, monitor=0)
    game.setDisplays(host_window, main_window)

    game.begin()



    # if DEBUG:
    #     game.players = [
    #         Player(f"Stuart", None),
    #         Player(f"Maddie", None),
    #         Player(f"Koda", None)
    #     ]
    #     game.dc.scoreboard.refresh_players()


    song_player = game.song_player
    try:
        socket_controller.start()
    except PermissionError as e:
        permission_error()
        raise e

    r = app.exec()


    # finally:
    #     logging.info("terminated")
    #     if song_player:
    #         song_player.stop()
    #     if not DEBUG:
    #         try:
    #             sys.exit(r)
    #         except NameError:
    #             sys.exit(1)
