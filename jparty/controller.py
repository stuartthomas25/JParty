import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.options import define, options

import os
from threading import Thread
import socket

from jparty.environ import root
from jparty.game import Player
from jparty.constants import MAXPLAYERS, PORT


define("port", default=PORT, help="run on the given port", type=int)


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
        if not self.get_cookie("test"):
            self.set_cookie("test", "test_val")
            logging.info("set cookie")
        else:
            logging.info(f"cookie: {self.get_cookie('test')}")
        self.render("play.html", messages=BuzzerSocketHandler.cache)


class BuzzerSocketHandler(tornado.websocket.WebSocketHandler):
    cache = []
    cache_size = 400

    def initialize(self):
        # self.name = None
        self.controller = self.application.controller
        self.player = None

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        self.set_nodelay(True)

    def send(self, msg, text=""):
        data = {"message": msg, "text": text}
        try:
            self.write_message(data)
            logging.info(f"Sent {data}")
        except:
            logging.error(f"Error sending message {msg}", exc_info=True)

    def check_if_exists(self, token, buzzerColor):
        logging.info(f"buzzer color 1: {buzzerColor}")

        p = self.controller.player_with_token(token, buzzerColor)
        if p is None:
            if token == "":
                logging.info("Buzzer pressed but no associated player")
                self.send("UNUSED_BUZZER")
                return
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
            logging.info(f"received buzzer press")
            if self.player == None:
                logging.info(f"no player associated with this buzzer; skipping")
                self.send("UNUSED_BUZZER")
                return
            self.buzz()
            return
        logging.info(f"received json message: {message}")
        parsed = tornado.escape.json_decode(message)
        msg = parsed["message"]
        text = parsed["text"]
        if msg == "NAME":
            buzzerColor = parsed["buzzerColor"]
            logging.info(f"received NAME: {text}")
            self.init_player(text, buzzerColor)
        elif msg == "CHECK_IF_EXISTS":
            logging.info(f"Checking if {text} exists")
            buzzerColor = None
            if "buzzerColor" in parsed:
                buzzerColor = parsed["buzzerColor"]
            self.check_if_exists(text, buzzerColor)
        elif msg == "WAGER":
            self.wager(text)
        elif msg == "ANSWER":
            self.application.controller.answer(self.player, text)

        else:
            raise Exception("Unknown message")

    def init_player(self, name, buzzerColor):

        if not self.controller.accepting_players:
            logging.info("Game started!")
            self.send("GAMESTARTED")
            return

        if len(self.controller.connected_players) >= MAXPLAYERS:
            self.send("FULL")
            return

        self.player = Player(name, buzzerColor, self)
        self.application.controller.new_player(self.player)
        logging.info(
            f"New Player: {self.player} {self.request.remote_ip} {self.player.token.hex()}"
        )
        self.send("TOKEN", self.player.token.hex())

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

    def start(self, threaded=True, tries=0):
        try:
            self.app.listen(self.port)
        except OSError as e:
            if tries>10:
                raise Exception("Cannot find open port")
            self.port += 1
            self.start(threaded, tries+1)
            return

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
        i_player = self.game.players.index(player)
        self.game.wager_trigger.emit(i_player, amount)

    def answer(self, player, guess):
        if self.game:
            self.game.answer(player, guess)
            player.page = "null"

    def new_player(self, player):
        self.connected_players.append(player)
        self.game.new_player_trigger.emit()

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

    def player_with_token(self, token, buzzerColor):
        for p in self.connected_players:
            logging.info(f"{p.token}, {token}")
            if p.token.hex() == token:
                logging.info("PLAYER MATCH")
                return p
            if buzzerColor != None and p.buzzercolor == buzzerColor:
                logging.info("PLAYER MATCH by buzzer color")
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
