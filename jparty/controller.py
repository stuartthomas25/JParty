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

define("port", default=80, help="run on the given port", type=int)


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

    def check_if_exists(self, token):
        p = self.controller.player_with_token(token)
        if p is not None:
            logging.info(f"Reconnected as {p.name}")
            self.player = p
            p.connected = True
            p.waiter = self
            self.send("EXISTS", p.page)

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
            logging.info(f"Checking if {parsed['text']} exists")
            self.check_if_exists(text)
        elif msg == "WAGER":
            self.wager(text)
        elif msg == "ANSWER":
            self.application.controller.answer(self.player, text)

        else:
            raise Exception("Unknown message")

    def init_player(self, name):

        if len(self.controller.connected_players) >= 8:
            logging.info("Game full!")
            self.send("GAMEFULL")
            return

        for p in self.controller.connected_players:
            if p.name == name:
                logging.info("Name taken!")
                self.send("NAMETAKEN")
                return
            elif name == "":
                return

        self.player = Player(name, self)
        self.application.controller.new_player(self.player)
        logging.info(
            f"New Player: {name} {self.request.remote_ip} {self.player.token.hex()}"
        )
        self.send("TOKEN", self.player.token.hex())
        # self.send("PROMPTWAGER", 69)

    def buzz(self):
        self.application.controller.buzz(self.player)

    def wager(self, text):
        self.application.controller.wager(self.player, int(text))
        self.player.page = "null"

    def send(self, msg, text=""):
        data = {"message": msg, "text": text}
        try:
            self.write_message(data)
            logging.info(f"Sent {data} to {self.player.name}")
        except:
            logging.error(f"Error sending message {msg}", exc_info=True)

    def on_close(self):
        pass
        # self.application.controller.buzzer_disconnected(self.player)


class BuzzerController:
    def __init__(self):
        self.thread = None
        self.game = None
        self.welcome_window = None
        tornado.options.parse_command_line()
        self.app = Application(
            self
        )  # this is to remove sleep mode on Macbook network card
        self.port = options.port
        self.connected_players = []

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
        self.game = None

    def buzz(self, player):
        if self.game:
            i_player = self.game.players.index(player)
            self.game.buzz_trigger.emit(i_player)
        else:
            i_player = self.connected_players.index(player)
            self.welcome_window.buzz_hint_trigger.emit(i_player)

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
        self.welcome_window.new_player(player)

    # def activate_buzzer(self, name):
    # BuzzerSocketHandler.activate_buzzer(name)

    @classmethod
    def localip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

    # hostname = socket.gethostname()
    # try:
    # ip = socket.gethostbyname(hostname)
    # if ip.startswith("127."):
    # raise Exception()
    # return ip
    # except:
    # return hostname

    # return [
    # l
    # for l in (
    # [
    # ip
    # for ip in socket.gethostbyname_ex(socket.gethostname())[2]
    # if not ip.startswith("127.")
    # ][:1],
    # [
    # [
    # (s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close())
    # for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]
    # ][0][1]
    # ],
    # )
    # if l
    # ][0][0]

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
