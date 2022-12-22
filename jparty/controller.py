#!/usr/bin/env python

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket

# import tornado.speedups
import os
import uuid
import time
from threading import Thread
import socket
from .environ import root
from .game import Player

from PyQt6.QtWidgets import QApplication

from tornado.options import define, options

define("port", default=8080, help="run on the given port", type=int)

MAXPLAYERS = 8

class Application(tornado.web.Application):
    def __init__(self, controller):
        handlers = [
            (r"/", WelcomeHandler),
            (r"/play", BuzzerHandler),
            (r"/buzzersocket", BuzzerSocketHandler),
        ]
        settings = dict(
            cookie_secret="",
            template_path=os.path.join(os.path.join(root, "buzzer", "templates")),
            static_path=os.path.join(root, "buzzer", "static"),
            xsrf_cookies=False,
            websocket_ping_interval=0.19,
        )
        super(Application, self).__init__(handlers, **settings)
        self.controller = controller


class WelcomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", messages=BuzzerSocketHandler.cache)


class BuzzerHandler(tornado.web.RequestHandler):
    def post(self):
        # self.set_header("Content-Type", "text/html")
        playername = self.get_body_argument("playername")
        if not self.get_cookie("test"):
            self.set_cookie("test", "test_val")
            logging.info("set cookie")
        else:
            logging.info(f"cookie: {self.get_cookie('test')}")
        # global playernames
        # playernames[self.request.remote_ip] = playername
        self.render("play.html", messages=BuzzerSocketHandler.cache)


max_waiters = 8


class BuzzerSocketHandler(tornado.websocket.WebSocketHandler):
    # waiters = set()
    cache = []
    cache_size = 400
    # player_names = {}

    def initialize(self):
        # self.name = None
        self.controller = self.application.controller
        self.player = None

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        self.set_nodelay(True)
        # self.controller.connected_players.add(self)

    def send(self, msg, text=""):
        data = {"message": msg, "text": text}
        try:
            self.write_message(data)
            logging.info(f"Sent {data}")
        except:
            logging.error(f"Error sending message {msg}", exc_info=True)

    def check_if_exists(self, token):


        p = self.controller.player_with_token(token)
        if p is None:
            logging.info("NEW")
            self.send("NEW")
        else:
            logging.info(f"Reconnected {p}")
            self.player = p
            p.connected = True
            p.waiter = self
            self.send("EXISTS", tornado.escape.json_encode(p.state()))


    def on_message(self, message):
        # do this first to kill latency
        if "BUZZ" in message:
            # logging.info("buzz")
            self.buzz()
            return
        parsed = tornado.escape.json_decode(message)
        msg = parsed["message"]
        text = parsed["text"]
        if msg == "NAME":
            self.init_player(text)
        elif msg == "CHECK_IF_EXISTS":
            logging.info(f"Checking if {self.player} exists")
            self.check_if_exists(text)
        elif msg == "WAGER":
            self.wager(text)
        elif msg == "ANSWER":
            self.application.controller.answer(self.player, text)

        else:
            raise Exception("Unknown message")

    def init_player(self, name):

        if not self.controller.accepting_players:
            logging.info("Game started!")
            self.send("GAMESTARTED")
            return

        if len(self.controller.connected_players) >= MAXPLAYERS:
            self.send("FULL")
            return

        self.player = Player(name, self)
        self.application.controller.new_player(self.player)
        logging.info(
            f"New Player: {self.player} {self.request.remote_ip} {self.player.token.hex()}"
        )
        self.send("TOKEN", self.player.token.hex())
        # self.send("PROMPTWAGER", 69)

    def buzz(self):
        self.application.controller.buzz(self.player)

    def wager(self, text):
        self.application.controller.wager(self.player, int(text))
        self.player.page = "null"

    def toolate(self):
        self.send("TOOLATE")

    def on_close(self):
        pass


class BuzzerController:
    def __init__(self, game):
        self.thread = None
        self.game = game
        tornado.options.parse_command_line()
        self.app = Application(
            self
        )  # this is to remove sleep mode on Macbook network card
        self.port = options.port
        self.connected_players = []
        self.accepting_players = True

    def start(self, threaded=True):
        self.app.listen(self.port)
        if threaded:
            self.thread = Thread(target=tornado.ioloop.IOLoop.current().start)
            self.thread.setDaemon(True)
            self.thread.start()
        else:
            tornado.ioloop.IOLoop.current().start()

    def restart(self):
        for p in self.connected_players:
            p.waiter.close()
        self.connected_players = []
        self.accepting_players = True

    def buzz(self, player):
        if self.game:
            i_player = self.game.players.index(player)
            self.game.buzz_trigger.emit(i_player)
        else:
            i_player = self.connected_players.index(player)
            self.game.buzz_hint_trigger.emit(i_player)

    def wager(self, player, amount):
        # self.game.wager(player, amount)
        i_player = self.game.players.index(player)
        self.game.wager_trigger.emit(i_player, amount)

    def answer(self, player, guess):
        if self.game:
            self.game.answer(player, guess)
            player.page = "null"

    def new_player(self, player):
        self.connected_players.append(player)
        self.game.new_player_trigger.emit()

    # def activate_buzzer(self, name):
    # BuzzerSocketHandler.activate_buzzer(name)

    @classmethod
    def localip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", options.port))
        return s.getsockname()[0]

    def host(self):
        localip = BuzzerController.localip()
        if self.port == 80:
            return f"{localip}"
        else:
            return f"{localip}:{self.port}"

    def player_with_token(self, token):
        for p in self.connected_players:
            logging.info(f"{p.token}, {token}")
            if p.token.hex() == token:
                logging.info("MATCH")
                return p
        return None

    def open_wagers(self, players=None):
        if players is None:
            players = self.connected_players

        for p in players:
            p.waiter.send("PROMPTWAGER", str(max(p.score, 0)))
            p.page = "wager"

    def prompt_answers(self):
        for p in self.connected_players:
            p.waiter.send("PROMPTANSWER")
            p.page = "answer"

    def toolate(self):
        for p in self.connected_players:
            p.waiter.send("TOOLATE")

        # self.welcome_window.buzzer_disconnected(player.name)
        # QApplication.instance().thread().finished.connect(self.welcome_window.buzzer_disconnected)
        # self.welcome_window.signal.connect(self.welcomeb
