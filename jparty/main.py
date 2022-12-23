import sys
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtWidgets import QApplication, QMessageBox
import requests
import logging


from jparty.game import Game
from jparty.controller import BuzzerController
from jparty.main_display import DisplayWindow, HostDisplayWindow
from jparty.style import JPartyStyle
from jparty.utils import resource_path


def check_internet():
    """check internet connection"""
    try:
        requests.get("http://www.j-archive.com/")
    except requests.exceptions.ConnectionError:  # This is the correct syntax
        QMessageBox.critical(
            None,
            "Cannot connect!",
            "JParty cannot connect to the J-Archive. Please check your internet connection.",
            buttons=QMessageBox.StandardButton.Abort,
            defaultButton=QMessageBox.StandardButton.Abort,
        )
        exit(1)


def permission_error():
    QMessageBox.critical(
        None,
        "Permission Error",
        "JParty encountered a permissions error when trying to listen on port 80.",
        buttons=QMessageBox.StandardButton.Abort,
        defaultButton=QMessageBox.StandardButton.Abort,
    )


def check_second_monitor():
    pass

    if len(QApplication.instance().screens()) < 2:
        print("error!")
        msgBox = QMessageBox()
        msgBox.setText(
            "JParty needs two separate displays. Please attach a second monitor or turn off mirroring and try again."
        )
        msgBox.exec()
        sys.exit(1)


def main():

    song_player = None
    r = 1

    QApplication.setStyle(JPartyStyle())
    app = QApplication(sys.argv)
    check_second_monitor()
    check_internet()
    app.setFont(QFont("Verdana"))

    try:
        QFontDatabase.addApplicationFont(
            resource_path("itc-korinna-std/ITC Korinna Regular.otf")
        )

        game = Game()
        socket_controller = BuzzerController(game)
        game.setBuzzerController(socket_controller)

        main_window = DisplayWindow(game)
        host_window = HostDisplayWindow(game)
        game.setDisplays(host_window, main_window)

        game.begin()

        song_player = game.song_player

        try:
            socket_controller.start()
        except PermissionError as e:
            permission_error()
            raise e

        r = app.exec()

    finally:
        logging.info("terminated")
        if song_player:
            song_player.stop()

        sys.exit(r)
