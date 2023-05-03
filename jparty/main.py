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
from jparty.logger import qt_exception_hook
from jparty.constants import PORT


def check_internet():
    """check internet connection"""
    try:
        requests.get("http://www.j-archive.com/")
    except requests.exceptions.ConnectionError:  # This is the correct syntax
        logging.error("Connection Error")
        QMessageBox.critical(
            None,
            "Cannot connect!",
            "JParty cannot connect to the J-Archive. Please check your internet connection.",
            buttons=QMessageBox.StandardButton.Abort,
            defaultButton=QMessageBox.StandardButton.Abort,
        )
        exit(1)


def permission_error():
    logging.error(f"Cannot access port {PORT}")
    QMessageBox.critical(
        None,
        "Permission Error",
        f"JParty encountered a permissions error when trying to listen on port {PORT}.",
        buttons=QMessageBox.StandardButton.Abort,
        defaultButton=QMessageBox.StandardButton.Abort,
    )


def check_second_monitor():
    if len(QApplication.instance().screens()) < 2:
        logging.error("No two monitors")
        QMessageBox.critical(
            None,
            "Two monitors needed!",
            "JParty needs two separate displays. Please attach a second monitor or turn off mirroring and try again.",
            buttons=QMessageBox.StandardButton.Abort,
            defaultButton=QMessageBox.StandardButton.Abort,
        )
        sys.exit(1)


def main():

    song_player = None
    r = 1  # default return code

    QApplication.setStyle(JPartyStyle())
    app = QApplication(sys.argv)

    check_second_monitor()
    check_internet()
    app.setFont(QFont("Verdana"))

    try:
        QFontDatabase.addApplicationFont(
            resource_path("ITC Korinna Regular.otf")
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
