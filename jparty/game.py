from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import QInputDialog, QApplication, QDialog, QVBoxLayout, QPushButton, QSpinBox, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

import threading
import time
from dataclasses import dataclass
import os
import sys
import simpleaudio as sa
from collections.abc import Iterable
import logging
import json
import requests
import datetime
import http.server
import socketserver

from jparty.utils import SongPlayer, resource_path, CompoundObject
from jparty.constants import FJTIME, QUESTIONTIME, VIDEO_PORT
from jparty.stats import StatsBox


class QuestionTimer(object):
    def __init__(self, interval, f, *args, **kwargs):
        super().__init__()
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.interval = interval
        self.__thread = None
        self.__start_time = None
        self.__elapsed_time = 0

    def run(self, i):
        thread = self.__thread
        time.sleep(i)
        if thread == self.__thread:
            self.f(*self.args, **self.kwargs)

    def start(self):
        """wrapper for resume"""
        self.resume()

    def cancel(self):
        """wrapper for pause"""
        self.pause()

    def pause(self):
        self.__thread = None
        self.__elapsed_time += time.time() - self.__start_time

    def resume(self):
        self.__thread = threading.Thread(
            target=self.run, args=(self.interval - self.__elapsed_time,)
        )
        self.__thread.start()
        self.__start_time = time.time()


@dataclass
class KeystrokeEvent:
    key: int
    func: callable
    hint_setter: callable = None
    active: bool = False
    persistent: bool = False


class KeystrokeManager(object):
    def __init__(self):
        super().__init__()
        self.__events = {}

    def addEvent(
        self, ident, key, func, hint_setter=None, active=False, persistent=False
    ):
        self.__events[ident] = KeystrokeEvent(
            key, func, hint_setter, active, persistent
        )

    def call(self, key):
        """this is split in to two for loops so one execution doesnt cause another event to trigger"""
        events_to_call = []
        for ident, event in self.__events.items():
            if event.active and event.key == key:
                logging.info(f"Calling {ident}")
                events_to_call.append(event)
                if not event.persistent:
                    self._deactivate(ident)

        for event in events_to_call:
            event.func()

    def _activate(self, ident):
        logging.info(f"Activating {ident}")
        e = self.__events[ident]
        e.active = True
        e.hint_setter(True)
        if e.hint_setter:
            e.hint_setter(True)

    def _deactivate(self, ident):
        e = self.__events[ident]
        e.active = False
        if e.hint_setter:
            e.hint_setter(False)

    def activate(self, *idents):
        if isinstance(idents, Iterable):
            for ident in idents:
                self._activate(ident)
        else:
            self._activate(idents)

    def deactivate(self, *idents):
        if isinstance(idents, Iterable):
            for ident in idents:
                self._deactivate(ident)
        else:
            self._deactivate(idents)


@dataclass
class Question:
    index: tuple
    text: str
    answer: str
    category: str
    image_link: str = None
    video_link: str = None
    includes_audio: bool = False
    image_content: str = None
    value: int = -1
    dd: bool = False
    complete: bool = False
    


class Board(object):
    size = (6, 5)

    def __init__(self, categories, questions, dj=False):
        self.categories = categories
        self.dj = dj
        if not questions is None:
            self.questions = questions
        else:
            self.questions = []

    def get_question(self, i, j):
        for q in self.questions:
            if q.index == (i, j):
                return q
        return None

    def complete(self):
        return len(self.questions) == 30


class FinalBoard(Board):
    size = (1, 1)

    def __init__(self, category, question):
        super().__init__([category], [question], dj=False)
        self.category = category
        self.question = question

    def complete(self):
        return len(self.questions) == 1


@dataclass
class GameData:
    rounds: list
    date: str
    comments: str


class Game(QObject):
    buzz_trigger = pyqtSignal(int)
    new_player_trigger = pyqtSignal()
    wager_trigger = pyqtSignal(int, int)
    toolate_trigger = pyqtSignal()

    def __init__(self):
        super().__init__()

        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

        with open(resource_path('theme_config.json'), 'r') as theme_config_file:
            self.theme_config = json.load(theme_config_file)

        print("theme_config:")
        print(self.theme_config)
        # Normalize color values from theme_config. Values are expected to be
        # hex strings like "#RRGGBB" (user-specified). We expose both the
        # raw hex string (for stylesheets) and a QColor (for painting).
        colors_block = self.theme_config.get("colors", self.theme_config)

        def _ensure_hash(s):
            if s is None:
                return None
            if isinstance(s, str) and s.startswith("#"):
                return s
            if isinstance(s, str):
                return f"#{s}"
            return None

        board_tile_color_hex = _ensure_hash(colors_block.get("boardTileColor")) or "#1E90FF"
        board_tile_highlighted_color_hex = _ensure_hash(colors_block.get("boardTileHighlightedColor")) or "#0B3D91"

        # Expose both hex (useful for stylesheets) and QColor (useful for painting)
        self.board_tile_color_hex = board_tile_color_hex
        self.board_tile_highlighted_color_hex = board_tile_highlighted_color_hex
        self.board_tile_color = QColor(self.board_tile_color_hex)
        self.board_tile_highlighted_color = QColor(self.board_tile_highlighted_color_hex)
        logging.info(
            f"Theme colors - board_tile_color: {self.board_tile_color_hex}, "
            f"board_tile_highlighted_color: {self.board_tile_highlighted_color_hex}"
        )

        self.host_display = None
        self.main_display = None
        self.dc = None

        self.data = None

        self.current_round = None
        self.players = []

        self.active_question = None
        self.accepting_responses = False
        self.accepting_responses_time = None
        self.answering_player = None
        self.previous_answerer = []
        self.timer = None
        self.soliciting_player = False  # part of selecting who found a daily double

        self.song_player = SongPlayer()
        self.__judgement_round = 0
        self.__sorted_players = None

        self.buzzer_controller = None

        self.keystroke_manager = KeystrokeManager()

        self.keystroke_manager.addEvent(
            "CORRECT_ANSWER", Qt.Key.Key_Left, self.correct_answer, self.arrowhints
        )
        self.keystroke_manager.addEvent(
            "INCORRECT_ANSWER", Qt.Key.Key_Right, self.incorrect_answer, self.arrowhints
        )
        self.keystroke_manager.addEvent(
            "BACK_TO_BOARD", Qt.Key.Key_Space, self.back_to_board, self.spacehints
        )
        self.keystroke_manager.addEvent(
            "OPEN_RESPONSES", Qt.Key.Key_Space, self.open_responses, self.spacehints
        )
        self.keystroke_manager.addEvent(
            "NEXT_ROUND", Qt.Key.Key_Space, self.next_round, self.spacehints
        )
        self.keystroke_manager.addEvent(
            "OPEN_FINAL", Qt.Key.Key_Space, self.open_final, self.spacehints
        )
        self.keystroke_manager.addEvent(
            "CLOSE_GAME", Qt.Key.Key_Space, self.close_game, self.spacehints
        )
        self.keystroke_manager.addEvent(
            "FINAL_OPEN_RESPONSES",
            Qt.Key.Key_Space,
            self.final_open_responses,
            self.spacehints,
        )
        self.keystroke_manager.addEvent(
            "FINAL_NEXT_PLAYER",
            Qt.Key.Key_Space,
            self.final_next_player,
            self.spacehints,
        )
        self.keystroke_manager.addEvent(
            "FINAL_SHOW_ANSWER",
            Qt.Key.Key_Space,
            self.final_show_answer,
            self.spacehints,
        )
        self.keystroke_manager.addEvent(
            "FINAL_CORRECT_ANSWER",
            Qt.Key.Key_Left,
            self.final_correct_answer,
            self.arrowhints,
        )
        self.keystroke_manager.addEvent(
            "FINAL_INCORRECT_ANSWER",
            Qt.Key.Key_Right,
            self.final_incorrect_answer,
            self.arrowhints,
        )
        self.keystroke_manager.addEvent(
            "ADMIN_SKIP_QUESTION",
            Qt.Key.Key_0,
            self.admin_skip_question,
            self.adminhints,
        )
        self.keystroke_manager.addEvent(
            "ADMIN_SKIP_ROUND",
            Qt.Key.Key_F5,
            self.admin_skip_round,
            self.adminhints,
        )
        self.keystroke_manager.activate("ADMIN_SKIP_ROUND")
        self.keystroke_manager.addEvent(
            "ADMIN_SHOW_STATS",
            Qt.Key.Key_Tab,
            self.show_stats,
            self.adminhints,
            persistent=True
        )
        self.keystroke_manager.activate("ADMIN_SHOW_STATS")

        self.wager_trigger.connect(self.wager)
        self.buzz_trigger.connect(self.buzz)
        self.new_player_trigger.connect(self.new_player)
        self.toolate_trigger.connect(self.__toolate)

        # Setup video server
        def run_server():
            with socketserver.TCPServer(("", VIDEO_PORT), http.server.SimpleHTTPRequestHandler) as httpd:
                print("Serving videos at port", VIDEO_PORT)
                httpd.serve_forever()

        # Create a new thread and start the server
        server_thread = threading.Thread(target=run_server)
        server_thread.start()

    def show_stats(self):
        stats_box = StatsBox(self.host_display)
        stats_box.exec()

    def startable(self):
        return self.valid_game() and len(self.buzzer_controller.connected_players) > 0

    def begin(self):
        self.song_player.play(repeat=True)

    def start_game(self):
        self.current_round = self.data.rounds[0]
        self.dc.hide_welcome_widgets()
        self.dc.board_widget.load_round(self.current_round)
        self.buzzer_controller.accepting_players = False
        self.song_player.stop()
        # Update config when game starts in case host made some settings changes
        with open('config.json', 'r') as f:
            self.config = json.load(f)

        # preload images for first round
        logging.info(f"Start game -> triggering image loading")
        threading.Thread(target=self.preload_images, args=(self.current_round,)).start()

    def setDisplays(self, host_display, main_display):
        self.host_display = host_display
        self.main_display = main_display
        self.dc = CompoundObject(host_display, main_display)

    def setBuzzerController(self, controller):
        self.buzzer_controller = controller

    def arrowhints(self, val):
        self.host_display.borders.arrowhints(val)

    def spacehints(self, val):
        self.host_display.borders.spacehints(val)
    
    def adminhints(self, val):
        pass

    def new_player(self):
        self.players = self.buzzer_controller.connected_players
        self.dc.scoreboard.refresh_players()
        self.host_display.welcome_widget.check_start()

    def remove_player(self, player):
        self.players.remove(player)
        player.waiter.close()
        self.dc.scoreboard.refresh_players()
        self.host_display.welcome_widget.check_start()

        # If the host removes a player in the final jeopardy round,
        # check if all remaining players have already wagered
        if isinstance(self.current_round, FinalBoard):
            self.check_if_all_wagered()
    
    def admin_skip_round(self):
        if isinstance(self.current_round, FinalBoard):
            return
        self.next_round()
        self.keystroke_manager.activate("ADMIN_SKIP_ROUND")
    
    def admin_skip_question(self):
        if not self.active_question:
            return
        self.keystroke_manager.deactivate("BACK_TO_BOARD", "OPEN_RESPONSES")
        self.accepting_responses = False
        self.dc.borders.lights(False)
        self.soliciting_player = False
        self.answer_given()
        self.back_to_board()

    def valid_game(self):
        return self.data is not None and all(b.complete() for b in self.data.rounds)

    def open_responses(self):
        self.dc.borders.lights(True)
        self.accepting_responses = True
        self.accepting_responses_time = datetime.datetime.now()

        # Set stats for players who buzzed early
        for player in self.players:
            if player.buzz_time is not None:
                time_elapsed = datetime.datetime.now() - player.buzz_time
                self.dc.player_widget(player).update_stats(time_elapsed.total_seconds(), "early")
                player.buzz_time = None

        if not self.timer:
            self.timer = QuestionTimer(QUESTIONTIME, self.stumped)

        self.timer.start()

        if self.active_question.includes_audio:
            self.host_display.question_widget.hide_video()

    def close_responses(self):
        self.timer.pause()
        self.accepting_responses = False
        self.dc.borders.lights(True)

    def buzz(self, i_player):
        player = self.players[i_player]

        if self.active_question is None:
            self.dc.player_widget(player).buzz_hint()
            return

        already_answered = False
        player_already_timed_out = player.istimedout

        # Check if player is already answering or timed out
        if player_already_timed_out == True or self.answering_player is player:
            return

        if self.accepting_responses and self.answering_player is None:
            # First buzz on time
            time_elapsed = datetime.datetime.now() - self.accepting_responses_time
            self.dc.player_widget(player).update_stats(time_elapsed.total_seconds(), "first")
        elif not self.accepting_responses and self.answering_player is None:
            # Buzzed in too early
            player.buzz_time = datetime.datetime.now()
        else:
            # Buzzed in after someone else
            time_elapsed = datetime.datetime.now() - self.accepting_responses_time
            self.dc.player_widget(player).update_stats(time_elapsed.total_seconds(), "late")

        # Check if player already answered incorrectly
        for prev_player in self.previous_answerer:
            if prev_player is player:
                already_answered = True

        if not self.accepting_responses:
            logging.info(f"player buzzed early")
            self.dc.player_widget(player).run_timeout_lights()
        elif not already_answered:
            logging.info(f"buzz ({time.time():.6f} s)")
            self.accepting_responses = False
            self.timer.pause()
            self.previous_answerer.append(player)
            self.dc.player_widget(player).run_lights()

            self.answering_player = player
            self.keystroke_manager.activate("CORRECT_ANSWER", "INCORRECT_ANSWER")
            self.dc.borders.lights(False)
        else:
            pass

    def answer_given(self):
        self.keystroke_manager.deactivate("CORRECT_ANSWER", "INCORRECT_ANSWER")
        if self.answering_player:
            self.dc.player_widget(self.answering_player).stop_lights()
            self.answering_player = None

    def back_to_board(self):
        logging.info("back_to_board")
        self.dc.hide_question()
        self.timer = None
        self.active_question.complete = True
        self.active_question = None
        self.previous_answerer = []
        if all(q.complete for q in self.current_round.questions):
            logging.info("Ready for next round")
            self.keystroke_manager.activate("ADMIN_SHOW_STATS", "NEXT_ROUND")
        
        # clear stats
        for player in self.players:
            self.dc.player_widget(player).clear_stats()

    def set_player_in_control(self, new_player):
        for player in self.players:
            # Remove glow around player widget
            self.host_display.player_widget(player).setGraphicsEffect(None)

        if new_player is not None:
            # Add white glow around player widget with offset 0, 0
            effect = QGraphicsDropShadowEffect()
            effect.setColor(QColor(255, 255, 255, 255))
            effect.setBlurRadius(100)
            effect.setOffset(0, 0)
            self.host_display.player_widget(new_player).setGraphicsEffect(effect)

    def next_round(self):
        logging.info("next round")
        i = self.data.rounds.index(self.current_round)
        self.current_round = self.data.rounds[i + 1]

        # Start preloading images in a separate thread
        threading.Thread(target=self.preload_images, args=(self.current_round,)).start()

        if isinstance(self.current_round, FinalBoard):
            self.set_player_in_control(None)

            self.dc.load_final(self.current_round.question)
            self.dc.show_player_kick_buttons()
            self.start_final()
        else:
            # Highlight player with least money to have control
            losing_player = min(self.players, key=lambda p: p.score)
            self.set_player_in_control(losing_player)

            self.dc.board_widget.load_round(self.current_round)

    def start_final(self):
        logging.info("start final")

        if self.config.get('allownegativeinfinal', 'True') == 'True':
            for player in self.players:
                self.dc.player_widget(player).set_lights(True)
        else:
            for player in self.players.copy():  # Use copy for iteration
                if player.score < 0:
                    self.remove_player(player)  # Remove from original list
                else:
                    self.dc.player_widget(player).set_lights(True)

        self.buzzer_controller.open_wagers()
    
    def preload_images(self, round):
        logging.info(f"Starting to pre-load images")
        for question in round.questions:
            if question.image_link is not None:
                self.load_image(question)
                # Delay to avoid rate limit from website
                time.sleep(2)

    def load_image(self, question):
        try:
            logging.info(f"pre-loading image: {question.image_link}")
            request = requests.get(question.image_link, timeout=1)
            question.image_content = request.content
            logging.info(f"loaded image: {question.image_link}")

        except requests.Timeout:
            # Some websites always timeout and load forever, maybe because it detects that it's a bot
            # Set the image content to "Not Found" to avoid trying to load it again
            logging.info(f"timed out loading image: {question.image_link}")
            question.image_content = b"Not Found"
        except requests.exceptions.RequestException as e:
            logging.info(f"failed to load image: {question.image_link}")

    def wager(self, i_player, amount):
        player = self.players[i_player]
        player.wager = amount
        self.dc.player_widget(player).set_lights(False)
        logging.info(f"{player} wagered {amount}")
        self.check_if_all_wagered()

    def answer(self, player, guess):
        player.finalanswer = guess
        logging.info(f"{player} guessed {guess}")
    
    def check_if_all_wagered(self):
        if all(p.wager is not None for p in self.players):
            self.host_display.question_widget.hint_label.setText(
                "Press space to show clue!"
            )
            self.keystroke_manager.activate("OPEN_FINAL")

    def final_open_responses(self):
        self.dc.hide_player_kick_buttons()
        self.dc.borders.lights(True)
        self.buzzer_controller.prompt_answers()

        self.song_player.final()

        self.timer = QuestionTimer(FJTIME, self.final_finished_song)
        self.timer.start()

    def final_next_player(self):
        for p in self.players:
            self.dc.player_widget(p).set_lights(False)

        if self.__judgement_round == 0:
            self.dc.load_final_judgement()
            self.__sorted_players = sorted(self.players, key=lambda x: x.score)

        elif self.__judgement_round == len(self.players):
            self.end_game()
            return

        self.answering_player = self.__sorted_players[self.__judgement_round]

        self.dc.player_widget(self.answering_player).set_lights(True)

        self.dc.final_window.guess_label.setText("")
        self.dc.final_window.wager_label.setText("")

        self.keystroke_manager.activate("FINAL_SHOW_ANSWER")

    def final_show_answer(self):
        answer = self.answering_player.finalanswer
        if answer == "":
            answer = "________"

        self.dc.final_window.guess_label.setText(answer)
        self.keystroke_manager.activate(
            "FINAL_CORRECT_ANSWER", "FINAL_INCORRECT_ANSWER"
        )

    def final_correct_answer(self):
        ap = self.answering_player
        self.set_score(ap, ap.score + ap.wager)
        self.final_judgement_given()

    def final_incorrect_answer(self):
        ap = self.answering_player
        self.set_score(ap, ap.score - ap.wager)
        self.final_judgement_given()

    def final_judgement_given(self):
        self.keystroke_manager.deactivate(
            "FINAL_CORRECT_ANSWER", "FINAL_INCORRECT_ANSWER"
        )
        self.dc.final_window.wager_label.setText(str(self.answering_player.wager))
        self.keystroke_manager.activate("FINAL_NEXT_PLAYER")
        self.__judgement_round += 1

    def final_finished_song(self):
        logging.info("Final song ended")
        self.toolate_trigger.emit()
        self.accepting_responses = False
        self.dc.borders.flash()
        self.keystroke_manager.activate("FINAL_NEXT_PLAYER")

    def end_game(self):
        top_score = max([p.score for p in self.players])
        winners = [p for p in self.players if p.score == top_score]
        for w in winners:
            self.dc.player_widget(w).set_lights(True)

        if len(winners) == 1:
            self.dc.final_window.show_winner(winners[0])
        else:
            self.dc.final_window.show_tie()

        wo = sa.WaveObject.from_wave_file(resource_path("applause.wav"))
        wo.play()

        print("activate close game")
        self.keystroke_manager.activate("CLOSE_GAME")

    def close_game(self):
        self.buzzer_controller.restart()
        self.players = []
        self.current_round = None
        self.answering_player = None
        self.timer = None
        self.data = None
        self.__judgement_round = 0
        self.dc.restart()
        self.begin()

    def get_dd_wager(self, player):
        self.answering_player = player
        self.soliciting_player = False

        if self.current_round is self.data.rounds[0]:
            max_wager = max(self.answering_player.score, 1000)
        else:
            max_wager = max(self.answering_player.score, 2000)

        wager_dialog = WagerDialog(max_wager, self.host_display)

        if wager_dialog.exec() == QDialog.DialogCode.Rejected:
            self.soliciting_player = True
            return False

        wager = wager_dialog.get_wager()
        self.active_question.value = wager

        self.keystroke_manager.activate("CORRECT_ANSWER", "INCORRECT_ANSWER")
        self.dc.question_widget.show_question()

    def load_question(self, q):
        self.active_question = q
        self.keystroke_manager.activate("ADMIN_SKIP_QUESTION")
        if q.dd:
            logging.info("Daily double!")
            wo = sa.WaveObject.from_wave_file(resource_path("dd.wav"))
            wo.play()
            self.soliciting_player = True
        else:
            self.keystroke_manager.activate("OPEN_RESPONSES")
        self.dc.load_question(q)
        self.dc.remove_card(q)

    def open_final(self):
        self.dc.question_widget.show_question()
        wo = sa.WaveObject.from_wave_file(resource_path("ding.wav"))
        wo.play()
        self.keystroke_manager.activate("FINAL_OPEN_RESPONSES")

    def correct_answer(self):
        if self.timer:
            self.timer.cancel()

        self.set_score(
            self.answering_player,
            self.answering_player.score + self.active_question.value,
        )
        self.answering_player.stats["correct"] += 1
        self.answering_player.stats["revenue"] += self.active_question.value
        self.set_player_in_control(self.answering_player)
        self.dc.borders.lights(False)
        self.answer_given()
        self.back_to_board()

    def incorrect_answer(self):
        if self.config.get('allownegative', 'True') == 'True':
            self.set_score(
                self.answering_player,
                self.answering_player.score - self.active_question.value,
            )
        else:
            self.set_score(
                self.answering_player,
                self.answering_player.score - 0,
            )
        
        self.answering_player.stats["incorrect"] += 1
        self.answering_player.stats["losses"] += self.active_question.value
        self.answer_given()
        if self.active_question.dd:
            self.back_to_board()
        else:
            self.open_responses()
            self.timer.resume()

    def stumped(self):
        self.accepting_responses = False
        sa.WaveObject.from_wave_file(resource_path("stumped.wav")).play()
        self.dc.borders.flash()
        self.keystroke_manager.activate("BACK_TO_BOARD")

    def __toolate(self):
        self.buzzer_controller.toolate()

    def set_score(self, player, score):
        player.score = score
        self.dc.player_widget(player).update_score()

    def adjust_score(self, player):
        new_score, answered = QInputDialog.getInt(
            self.host_display,
            "Adjust Score",
            "Enter a new score:",
            value=player.score,
        )
        if answered:
            self.set_score(player, new_score)

    def close(self):
        self.song_player.stop()
        QApplication.quit()


class Player(object):
    def __init__(self, name, buzzerColor, waiter):
        logging.info(f"Player init received buzzerColor: {buzzerColor}")
        self.buzzercolor = buzzerColor
        self.name = name
        self.token = os.urandom(15)
        self.score = 0
        self.waiter = waiter
        self.wager = None
        self.finalanswer = ""
        self.page = "buzz"
        self.istimedout = False
        
        # Stats
        self.buzz_time = None
        self.buzz_delays = []
        self.stats = {
            "correct": 0,
            "incorrect": 0,
            "revenue": 0,
            "losses": 0,
        }

    def __hash__(self):
        return int.from_bytes(self.token, sys.byteorder)

    def state(self):
        return {"page": self.page, "score": self.score}

class WagerDialog(QDialog):
    def __init__(self, max_wager, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Wager")

        self.layout = QVBoxLayout(self)

        self.prompt_label = QLabel(f"Enter the players wager, the player can wager up to ${max_wager}", self)
        self.layout.addWidget(self.prompt_label)

        self.spinBox = QSpinBox(self)
        self.spinBox.setRange(0, max_wager)
        self.layout.addWidget(self.spinBox)

        self.true_daily_double_button = QPushButton("True Daily Double (Max Wager)", self)
        self.true_daily_double_button.clicked.connect(self.set_max_wager)
        self.layout.addWidget(self.true_daily_double_button)

        self.submit_button = QPushButton("Submit Wager", self)
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)

    def set_max_wager(self):
        self.spinBox.setValue(self.spinBox.maximum())

    def get_wager(self):
        return self.spinBox.value()