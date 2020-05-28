from types import SimpleNamespace
from PyQt5.QtCore import Qt
import threading
import time
from dataclasses import dataclass

class QuestionTimer(object):
    def __init__(self, interval, f, *args, **kwargs):
        super().__init__()
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.interval = interval
        self.__thread = None
        self.__start_time = -1
        self.__elapsed_time = 0

    def run(self, i):
        thread = self.__thread
        time.sleep(i)
        if thread == self.__thread:
            self.f(*self.args, **self.kwargs)

    def start(self):
        '''wrapper for resume'''
        self.resume()

    def cancel(self):
        '''wrapper for resume'''
        self.pause()

    def pause(self):
        self.__thread = None
        self.__elapsed_time += (time.time() - self.__start_time)

    def resume(self):
        self.__thread = threading.Thread(target=self.run, args=(self.interval - self.__elapsed_time,))
        self.__thread.start()
        self.__start_time = time.time()

@dataclass
class KeystrokeEvent:
    key: int
    func: callable
    active: bool = False
    persistent: bool = True

class KeystrokeManager(object):
    def __init__(self):
        super().__init__()
        self.__events = {}
    def addEvent(self,ident,key,func,active=False, persistent=True):
        self.__events[ident] = KeystrokeEvent(key, func, active, persistent)

    def call(self, key):
        for ident, event in self.__events.items():
            if event.active and event.key==key:
                event.func()
                if not event.persistent:
                    self.deactivate(ident)

    def activate(self, ident):
        self.__events[ident].active = True

    def deactivate(self, ident):
        self.__events[ident].active = False

class CompoundObject(object):
    def __init__(self, *objs):
        self.__objs = list(objs)

    def __setattr__(self, name, value):
        if name[0] == '_':
            self.__dict__[name] = value
        else:
            for obj in self.__objs:
                setattr(obj, name, value)

    def __getattr__(self, name):
        ret = CompoundObject(*[getattr(obj, name) for obj in self.__objs])
        return ret

    def __iadd__(self, display):
        self.__objs.append(display)
        return self

    def __call__(self, *args, **kwargs):
        return CompoundObject(*[obj(*args, **kwargs) for obj in self.__objs])

    def __repr__(self):
        return "CompoundObject("+", ".join([ repr(o) for o in self.__objs])+")"


class Question(object):
    def __init__(self,index,text,answer,value):
        self.index = index
        self.text = text
        self.answer = answer
        self.value = value

class Board(object):
    def __init__(self,categories, questions, final=False, dj=False):
        if final:
            self.size = (1,1)
        else:
            self.size = (6,5)
        self.final = final
        self.categories = categories
        self.dj = dj
        if not questions is None:
            self.questions = questions
        else:
            self.questions = []
    def get_question(self,i,j):
        for q in self.questions:
            if q.index == (i,j):
                return q
        return None
def updateUI(f):
    def wrapper(self, *args):
        ret = f(self, *args)
        self.update()
        return ret
    return wrapper

class Game(object):
    def __init__(self,rounds):
        self.rounds = rounds
        self.scores = {}
        self.dc = CompoundObject()
        self.paused = False
        self.active_question = None
        self.accepting_responses = False
        self.answering_player = None
        self.completed_questions = []
        self.already_answered = []
        self.timer = None

        self.buzzer_controller = None

        self.keystroke_manager = KeystrokeManager()
        self.keystroke_manager.addEvent('OPEN_RESPONSES', Qt.Key_Space, self.open_responses)
        self.keystroke_manager.addEvent('CORRECT_RESPONSE', Qt.Key_Left, self.correct_answer)
        self.keystroke_manager.addEvent('INCORRECT_RESPONSE', Qt.Key_Right, self.incorrect_answer, persistent=False)
        self.keystroke_manager.addEvent('BACK_TO_BOARD', Qt.Key_Space, self.back_to_board, persistent=False)


    @updateUI
    def open_responses(self):
        self.accepting_responses = True
        self.dc.borderwidget.lit = True
        self.timer = QuestionTimer(4, self.stumped)
        self.timer.start()

    def update(self):
        self.dc.update()

    def buzz(self, player):
        if self.accepting_responses and not player in self.already_answered:
            self.timer.pause()
            self.already_answered.append(player)
            self.accepting_responses = False
            self.dc.scoreboard.highlight(player)
            self.dc.update()

            self.answering_player = player
            self.buzzer_controller.activate_buzzer(player)
            self.keystroke_manager.activate('CORRECT_RESPONSE')
            self.keystroke_manager.activate('INCORRECT_RESPONSE')

    def answer_given(self):
        self.dc.scoreboard.stop_lights()
        self.deactivate_responses()
        self.answering_player = None

    def deactivate_responses(self):
        self.keystroke_manager.deactivate('CORRECT_RESPONSE')
        self.keystroke_manager.deactivate('INCORRECT_RESPONSE')

    @updateUI
    def back_to_board(self):
        self.completed_questions.append(self.active_question)
        self.active_question = None
        self.already_answered = []

    @updateUI
    def correct_answer(self):
        self.timer.cancel()
        self.scores[self.answering_player] += self.active_question.value
        self.answer_given()
        self.back_to_board()
        self.dc.borderwidget.lit = False

    @updateUI
    def incorrect_answer(self):
        self.scores[self.answering_player] -= self.active_question.value
        self.answer_given()
        self.open_responses()
        self.timer.resume()

    @updateUI
    def stumped(self):
        self.deactivate_responses()
        self.accepting_responses = False
        self.flash()

    def flash(self):
        self.dc.borderwidget.lit = False
        time.sleep(0.2)
        self.dc.borderwidget.lit = True
        time.sleep(0.2)
        self.dc.borderwidget.lit = False
        self.keystroke_manager.activate('BACK_TO_BOARD')





game_params = SimpleNamespace()
game_params.money1 = [200,400,600,800,1000]
game_params.money2 = [400,800,1200,1600,2000]
