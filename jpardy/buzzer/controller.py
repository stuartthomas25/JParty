#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Simplified chat demo for websockets.

Authentication, error handling, etc are left as an exercise for the reader :)
"""

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
import time
from threading import Thread
import socket

from tornado.options import define, options

define("port", default=9999, help="run on the given port", type=int)



class Application(tornado.web.Application):
    def __init__(self, controller):
        handlers = [(r"/", WelcomeHandler), (r"/play", BuzzerHandler), (r"/buzzersocket", BuzzerSocketHandler)]
        settings = dict(
            cookie_secret="",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
        )
        super(Application, self).__init__(handlers, **settings)
        self.controller = controller


class WelcomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", messages=BuzzerSocketHandler.cache)

class BuzzerHandler(tornado.web.RequestHandler):
    def post(self):
        #self.set_header("Content-Type", "text/html")
        playername = self.get_body_argument("playername")
        if not self.get_cookie("test"):
            self.set_cookie("test","test_val")
            print("set cookie")
        else:
            print("cookie:", self.get_cookie("test"))
        # global playernames
        # playernames[self.request.remote_ip] = playername
        self.render("play.html", messages=BuzzerSocketHandler.cache)


max_waiters = 3

class BuzzerSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200
    player_names = {}

    def initialize(self):
        self.name = None

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        print(self.name,BuzzerSocketHandler.player_names)
        if len(BuzzerSocketHandler.waiters)>=3:
            print("Game full!")
            BuzzerSocketHandler.send("GAMEFULL", waiters=[self])
            return

        BuzzerSocketHandler.waiters.add(self)

    def on_close(self):
        BuzzerSocketHandler.waiters.remove(self)

    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size :]

    @classmethod
    def send_updates(cls, chat):
        logging.info("sending message to %d waiters", len(cls.waiters))
        print(f"sending message to {len(cls.waiters)} waiters")
        for waiter in cls.waiters:
            print()
            try:
                waiter.write_message(chat)
            except:
                logging.error("Error sending message", exc_info=True)
    @classmethod
    def activate_buzzer(cls, name):
        print("Activating "+name+"'s buzzer")
        handler = cls.player_names[name]
        cls.send("YOURTURN", waiters=[handler])

    def on_message(self, message):
        #print(' >',message)
        parsed = tornado.escape.json_decode(message)
        msg = parsed["message"]
        if msg == "BUZZ":
            self.buzz()
        if msg == "NAME":
            self.init_player(parsed["text"])

    def init_player(self,name):
        if  name in BuzzerSocketHandler.player_names:
            print("Name taken!")
            BuzzerSocketHandler.send("NAMETAKEN", waiters=[self])
            return

        print("New Player:",name,self.request.remote_ip)
        BuzzerSocketHandler.player_names[name] = self
        self.name = name
        self.application.controller.new_player(self.name)

    def buzz(self):
        self.application.controller.buzz(self.name)

    @classmethod
    def send(cls, msg, text="", waiters=waiters):
        data = {"message": msg, "text": text}
        for waiter in waiters:
            try:
                waiter.write_message(data)
                print(f"Sent {data} to {waiters}")
            except:
                logging.error(f"Error sending message {msg}", exc_info=True)


class BuzzerController:
    def __init__(self):
        self.thread = None
        self.game = None
        self.welcome_window = None
        tornado.options.parse_command_line()
        self.app = Application(self)
        self.port = options.port

    def start(self,threaded=True):
        self.app.listen(self.port)
        if threaded:
            self.thread = Thread(target=tornado.ioloop.IOLoop.current().start)
            self.thread.setDaemon(True)
            self.thread.start()
        else:
            tornado.ioloop.IOLoop.current().start()
    def buzz(self, name):
        self.game.buzz(name)

    def new_player(self, name):
        self.welcome_window.new_player(name)

    def activate_buzzer(self, name):
        BuzzerSocketHandler.activate_buzzer(name)

    @classmethod
    def localip(self):
        return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] \
        if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), \
        s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, \
        socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

    def host(self):
        localip = BuzzerController.localip()
        return f"{localip}:{self.port}"






if __name__ == "__main__":
    BC = BuzzerController()
    BC.start(False)
