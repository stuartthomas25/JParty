from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import QInputDialog, QApplication, QDialog, QVBoxLayout, QPushButton, QSpinBox, QLabel


import threading
import time
from dataclasses import dataclass
import os
import sys
import simpleaudio as sa
from collections.abc import Iterable
import logging
import json

from jparty.utils import SongPlayer, resource_path, CompoundObject
from jparty.constants import FJTIME, QUESTIONTIME


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

        with open('config.json', 'r') as f:
            self.config = json.load(f)

        self.host_display = None
        self.main_display = None
        self.dc = None

        self.data = None

        self.current_round = None
        self.players = []

        self.active_question = None
        self.accepting_responses = False
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

        self.wager_trigger.connect(self.wager)
        self.buzz_trigger.connect(self.buzz)
        self.new_player_trigger.connect(self.new_player)
        self.toolate_trigger.connect(self.__toolate)

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

    def new_player(self):
        self.players = self.buzzer_controller.connected_players
        self.dc.scoreboard.refresh_players()
        self.host_display.welcome_widget.check_start()

    def remove_player(self, player):
        self.players.remove(player)
        player.waiter.close()
        self.dc.scoreboard.refresh_players()
        self.host_display.welcome_widget.check_start()

    def valid_game(self):
        return self.data is not None and all(b.complete() for b in self.data.rounds)

    def open_responses(self):
        self.dc.borders.lights(True)
        self.accepting_responses = True

        if not self.timer:
            self.timer = QuestionTimer(QUESTIONTIME, self.stumped)

        self.timer.start()

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

        if player_already_timed_out == True:
            logging.info(f"player is timed out")
            return

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
            logging.info("NEXT ROUND")
            self.keystroke_manager.activate("NEXT_ROUND")

    def next_round(self):
        logging.info("next round")
        i = self.data.rounds.index(self.current_round)
        logging.info(f"ROUND {i}")
        self.current_round = self.data.rounds[i + 1]

        if isinstance(self.current_round, FinalBoard):
            self.dc.load_final(self.current_round.question)
            self.start_final()
        else:
            self.dc.board_widget.load_round(self.current_round)

    def start_final(self):
        logging.info("start final")
        for player in self.players:
            self.dc.player_widget(player).set_lights(True)

        self.buzzer_controller.open_wagers()

    def wager(self, i_player, amount):
        player = self.players[i_player]
        player.wager = amount
        self.dc.player_widget(player).set_lights(False)
        logging.info(f"{player} wagered {amount}")
        if all(p.wager is not None for p in self.players):
            self.host_display.question_widget.hint_label.setText(
                "Press space to show clue!"
            )
            self.keystroke_manager.activate("OPEN_FINAL")

    def answer(self, player, guess):
        player.finalanswer = guess
        logging.info(f"{player} guessed {guess}")

    def final_open_responses(self):
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
        self.keystroke_manager.activate("FINAL_OPEN_RESPONSES")

    def correct_answer(self):
        if self.timer:
            self.timer.cancel()

        self.set_score(
            self.answering_player,
            self.answering_player.score + self.active_question.value,
        )
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