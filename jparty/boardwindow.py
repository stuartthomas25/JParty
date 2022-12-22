from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QImage,
    QColor,
    QFont,
    QPalette,
    QPixmap,
    QTextDocument,
    QTextOption,
    QGuiApplication,
    QFontMetrics,
    QTransform
)
from PyQt6.QtWidgets import *  # QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt6.QtCore import (
    Qt,
    QRectF,
    QRect,
    QPoint,
    QPointF,
    QTimer,
    QRect,
    QSize,
    QSizeF,
    QMargins,
    QEvent
)
from .version import version
import qrcode


from .welcome_widget import Welcome, QRWidget
import os
from .retrieve import get_game, get_game_sum, get_random_game
from .game import Board
from .utils import resource_path, SongPlayer, add_shadow, DynamicLabel
from .constants import DEBUG
from .helpmsg import helpmsg
import time
from threading import Thread, active_count, current_thread
import re
import logging
from base64 import urlsafe_b64decode

margin = 50
n = 8  # even integer
FONTSIZE = 10

BLUE = QColor("#1010a1")
DARKBLUE = QColor("#0b0b74")
# BLUE = QColor("#031591")
HINTBLUE = QColor("#041ec8")
YELLOW = QColor("#ffcc00")
RED = QColor("#ff0000")
BLACK = QColor("#000000")
GREY = QColor("#505050")
WHITE = QColor("#ffffff")
GREEN = QColor("#33cc33")


CARDPAL = QPalette()
CARDPAL.setColor(QPalette.ColorRole.Window, BLUE)
CARDPAL.setColor(QPalette.ColorRole.WindowText, WHITE)

BOARDSIZE = (6, 6)

CATFONT = QFont()
CATFONT.setBold(True)
CATFONT.setPointSize(24)
CATPEN = QPen(WHITE)

MONFONT = QFont(CATFONT)
MONFONT.setPointSize(50)
MONPEN = QPen(YELLOW)
TEXTPADDING = 20

QUFONT = QFont()
QUFONT.setPointSize(70)
QUMARGIN = 50

NAMEHEIGHT = 50
NAMEFONT = QFont()
NAMEFONT.setPointSize(20)
NAMEPEN = QPen(WHITE)
SCOREFONT = QFont()
SCOREFONT.setPointSize(50)
SCOREPEN = QPen(WHITE)
HOLEPEN = QPen(RED)
HIGHLIGHTPEN = QPen(BLUE)
HIGHLIGHTBRUSH = QBrush(WHITE)
HINTBRUSH = QBrush(HINTBLUE)

CORRECTBRUSH = QBrush(GREEN)
INCORRECTBRUSH = QBrush(RED)

LIGHTPEN = QPen(GREY)
LIGHTBRUSH = QBrush(RED)

BORDERWIDTH = 10
BORDERPEN = QPen(BLACK)
BORDERPEN.setWidth(BORDERWIDTH)
DIVIDERBRUSH = QBrush(WHITE)
DIVIDERWIDTH = 20

FILLBRUSH = QBrush(QColor("white"))
SCOREHEIGHT = 0.15
ANSWERHEIGHT = 0.15

ANSWERBARS = 30

FINALANSWERHEIGHT = 0.6

def updateUI(f):
    return f



class MyLabel(DynamicLabel):
    def __init__(self, text, initialSize, parent=None):
        super().__init__(text, initialSize, parent)
        self.font().setBold(True)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        add_shadow(self)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
        self.setPalette(palette)

        self.show()


# class QuestionLabel(MyLabel):
#     def __init__(self, text, initialSize, parent=None):
#         super().__init__(text, parent)
#         self.setStyleSheet("color: white;")
#         self.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         self.setWordWrap(True)
#         self.font = QFont("Helvetica")
#         self.font.setPointSize(fontsize)
#         self.setFont(self.font)

#         add_shadow(self)


class QuestionWidget(QWidget):
    def __init__(self, question, parent=None):
        super().__init__(parent)
        self.question = question
        self.setAutoFillBackground(True)

        self.main_layout = QVBoxLayout()
        self.question_label = MyLabel(question.text.upper(), self.startFontSize, self)

        self.question_label.setFont( QFont( "ITC Korinna" ) )
        self.main_layout.addWidget(self.question_label)
        self.setLayout(self.main_layout)

        self.setPalette(CARDPAL)
        self.show()

    def startFontSize(self):
        return self.width() * 0.05

class HostQuestionWidget(QuestionWidget):
    def __init__(self, question, parent=None):
        super().__init__(question, parent)


        self.question_label.setText(question.text)
        self.main_layout.setStretchFactor(self.question_label, 6)
        self.main_layout.addSpacing(self.main_layout.contentsMargins().top())
        self.answer_label = MyLabel(question.answer, self.startFontSize, self)
        self.answer_label.setFont( QFont( "ITC Korinna" ) )
        self.main_layout.addWidget(self.answer_label, 1)
        # self.setLayout(self.main_layout


    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setPen(QPen(QColor('white')))
        line_y = self.main_layout.itemAt(1).geometry().top()
        qp.drawLine(0, line_y, self.width(), line_y)


class DailyDoubleWidget(QuestionWidget):
    def __init__(self, question, parent=None):
        super().__init__(question, parent)
        self.question_label.setVisible(False)
        # if self.parent().alex():

        print("create dd label")
        self.dd_label = MyLabel("DAILY<br/>DOUBLE!", self.startDDFontSize, self)
        self.main_layout.replaceWidget(self.question_label, self.dd_label)

    def startDDFontSize(self):
        return self.width() * 0.2

    def show_question(self):
        self.main_layout.replaceWidget(self.dd_label, self.question_label)
        self.dd_label.deleteLater()
        self.dd_label = None
        self.question_label.setVisible(True)

class HostDailyDoubleWidget(HostQuestionWidget, DailyDoubleWidget):
    def __init__(self, question, parent=None):
        super().__init__(question, parent)
        self.answer_label.setVisible(False)

        self.main_layout.setStretchFactor(self.dd_label, 6)
        self.hint_label = MyLabel("Click the player below who found the Daily Double", self.startFontSize, self)
        self.main_layout.replaceWidget(self.answer_label, self.hint_label)
        self.main_layout.setStretchFactor(self.hint_label, 1)

    def show_question(self):
        super().show_question()
        self.main_layout.replaceWidget(self.hint_label, self.answer_label)
        self.hint_label.deleteLater()
        self.hint_label = None
        self.answer_label.setVisible(True)

        # self.answer_label.setVisible(False)

        # self.main_layout.setStretchFactor(self.question_label, 6)
        # self.answer_label = MyLabel(question.answer, self.startFontSize, self)
        # self.main_layout.addWidget(self.answer_label, 1)


class FinalJeopardyWidget(QuestionWidget):
    def __init__(self, question, parent=None):
        super().__init__(question, parent)
        self.question_label.setVisible(False)
        # if self.parent().alex():
        #     self.answer_label.setVisible(False)

        self.category_label = MyLabel(question.category, self.startCategoryFontSize, self)
        print('replace w cat')
        self.main_layout.replaceWidget(self.question_label, self.category_label)

    def startCategoryFontSize(self):
        return self.width() * 0.1

    def show_question(self):
        self.main_layout.replaceWidget(self.category_label, self.question_label)
        self.category_label.deleteLater()
        self.category_label = None
        self.question_label.setVisible(True)

class HostFinalJeopardyWidget(FinalJeopardyWidget, HostQuestionWidget):
    def __init__(self, question, parent):
        super().__init__(question, parent)
        self.answer_label.setVisible(False)

        # self.main_layout.setStretchFactor(self.category_label, 6)
        self.main_layout.setStretchFactor(self.question_label, 6)
        self.hint_label = MyLabel("Waiting for all players to wager...", self.startFontSize, self)
        self.main_layout.replaceWidget(self.answer_label, self.hint_label)
        print('replace w hint')
        self.main_layout.setStretchFactor(self.hint_label, 1)

    def hide_hint(self):
        self.hint_label.setVisible(True)

    def show_question(self):
        super().show_question()
        self.main_layout.replaceWidget(self.hint_label, self.answer_label)
        self.hint_label.deleteLater()
        self.hint_label = None
        self.answer_label.setVisible(True)

class FinalDisplay(QWidget):
    def __init__(self, game, parent):
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.answer_widget = FinalAnswerWidget(game, self)
        main_layout = QVBoxLayout()
        main_layout.addStretch(4)
        main_layout.addWidget( self.answer_widget, 2)
        main_layout.addStretch(3)
        self.setLayout( main_layout )

        self.show()

class FinalAnswerWidget(QWidget):
    def __init__(self, game, parent):
        super().__init__(parent)
        self.game = game
        self.winner_label = None

        self.main_layout = QVBoxLayout()
        self.guess_label = MyLabel("", self.startFontSize, self)
        self.wager_label = MyLabel("", self.startFontSize, self)

        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.guess_label, 5)
        self.main_layout.addWidget(self.wager_label, 5)
        self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)

        self.setPalette(CARDPAL)
        self.setAutoFillBackground(True)
        add_shadow(self)

        self.show()

    def startFontSize(self):
        return self.height() * 0.2

    def show_winner(self, winner):
        self.guess_label.setText("We have a winner!")
        self.wager_label.setText("")
        self.winner_label = NameLabel(winner.name, self)
        self.main_layout.replaceWidget(self.wager_label, self.winner_label)

    def show_tie(self):
        self.guess_label.setText("We have a tie!")
        self.wager_label.setText("")




class CardLabel(QWidget):
    margin = 0.1
    def __init__(self, text, parent=None):
        super().__init__(parent)

        self.label = MyLabel(text, self.startFontSize, parent=self)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, BLUE)
        palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
        self.setPalette(palette)

        self.setAutoFillBackground(True)

    def startFontSize(self):
        return self.height() * 0.6

    def labelRect(self):
        wmargin = int(CardLabel.margin * self.width())
        hmargin = int(CardLabel.margin * self.height())
        return self.rect().adjusted(wmargin, hmargin, -wmargin, -hmargin)

    def setText(self, text):
        self.label.setText(text)

    @property
    def text(self):
        return self.label.text()

    def resizeEvent(self, event):
        if self.height() == 0:
            return None

        self.label.setGeometry(self.labelRect())

class CategoryCard(CardLabel):
    pass


class QuestionCard(CardLabel):
    def __init__(self, game, question=None):
        self.game = game
        self.__question = question
        super().__init__(self.__moneytext())
        self.label.setStyleSheet("color: #ffcc00")


    @property
    def question(self):
        return self.__question

    def __moneytext(self):
        if self.question is not None and not self.question.complete:
            return "$" + str(self.question.value)
        else:
            return ""

    @question.setter
    def question(self, q):
        self.__question = q
        self.setText(self.__moneytext())

    def startFontSize(self):
        return self.height() * 0.8


    def inactive(self):
        return self.question is None or self.question.complete


class HostQuestionCard(QuestionCard):
    def __init__(self, game, question=None):
        super().__init__(game, question)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if self.inactive(): return None

        self.leaveEvent(None)
        self.game.load_question(self.question)

    def leaveEvent(self, event):
        if self.inactive(): return None

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, BLUE)
        self.setPalette(pal)

    def enterEvent(self, event):
        if self.inactive(): return None

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, DARKBLUE)
        self.setPalette(pal)


class BoardWidget(QWidget):
    rows = 6
    columns = 6

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game

        self.responses_open = False

        self.questionwidget = None
        self.question_labels = []

        self.grid_layout = QGridLayout()

        self.resizeEvent(None)

        for x in range(Board.size[0]):
            self.grid_layout.setRowStretch(x, 1.)
        for y in range(Board.size[1]+1):
            self.grid_layout.setColumnStretch(y, 1.)

        for x in range(Board.size[0]):
            for y in range(Board.size[1]+1):
                if y == 0:
                    label = CategoryCard("")
                    self.grid_layout.addWidget(label, 0, x)
                else:
                    if self.parent().host():
                        label = HostQuestionCard(game, None)
                    else:
                        label = QuestionCard(game, None)
                    self.question_labels.append(label)
                    self.grid_layout.addWidget(label, y, x)

        self.setLayout(self.grid_layout)
        self.show()

    def load_round(self, round):
        gl = self.grid_layout
        for x in range(Board.size[0]):
            for y in range(Board.size[1]+1):
                if y == 0:
                    # Categories
                    gl.itemAtPosition(y,x).widget().setText(round.categories[x])
                else:
                    # Questions
                    q = round.get_question(x,y-1)
                    gl.itemAtPosition(y,x).widget().question = q


    def resizeEvent(self, event):
        self.grid_layout.setSpacing(self.width() // 150)

    @property
    def board(self):
        return self.game.current_round

    def clear(self):
        gl = self.grid_layout
        for x in range(Board.size[0]):
            for y in range(Board.size[1]+1):
                if y == 0:
                    # Categories
                    gl.itemAtPosition(y,x).widget().setText("")
                else:
                    # Questions
                    gl.itemAtPosition(y,x).widget().question = None


# class MainBoardWidget(BoardWidget):
#     pass

# class HostBoardWidget(BoardWidget):
#     def load_question(self, q):
#         if q.dd:
#             self.questionwidget = HostDailyDoubleWidget(q, self)
#         else:
#             self.questionwidget = HostQuestionWidget(q, self)
#

class NameLabel(MyLabel):
    name_aspect_ratio = 1.3422
    def __init__(self, name, parent):
        self.signature = None
        super().__init__("", self.startNameFontSize, parent)

        if name[:21] == 'data:image/png;base64':
            i = QImage()
            i.loadFromData(urlsafe_b64decode(name[22:]), "PNG")
            self.signature = QPixmap.fromImage(i)
        else:
            self.setText(name)

        self.setGraphicsEffect(None)

    def startNameFontSize(self):
        return self.height() * 0.2

    def resizeEvent(self, event):
        if self.signature is not None:
            self.setPixmap(
                self.signature.scaled(
                    self.height() * NameLabel.name_aspect_ratio, self.height() ,
                    transformMode=Qt.TransformationMode.SmoothTransformation,
                )
            )


class PlayerWidget(QWidget):
    aspect_ratio = 0.732
    margin = 0.05

    def __init__(self, game, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.game = game
        self.__buzz_hint_thread = None
        self.__flash_thread = None
        self.__light_thread = None

        # if player.name[:21] == 'data:image/png;base64':
        #     i = QImage()
        #     i.loadFromData(urlsafe_b64decode(self.player.name[22:]), "PNG")
        #     self.signature = QPixmap.fromImage(i)
        #     self.name_label = DynamicLabel("", 0, self)
        # else:

        #     self.name_label = MyLabel(player.name, self.startNameFontSize, self)
        #     self.signature = None
        #
        self.name_label = NameLabel(player.name, self)

        self.score_label = MyLabel("$0", self.startScoreFontSize, self)

        self.resizeEvent(None)
        self.update_score()

        self.setMouseTracking(True)


        self.main_background = QPixmap( resource_path("player.png") )
        self.active_background= QPixmap( resource_path("player_active.png") )
        self.lights_backgrounds = [QPixmap( resource_path(f"player_lights{i}.png") ) for i in range(1,6)]
        self.background = self.main_background

        self.highlighted = False

        layout = QVBoxLayout()
        layout.addStretch(4)
        layout.addWidget(self.score_label, 10)
        layout.addStretch(10)
        layout.addWidget(self.name_label, 32)
        layout.addStretch(10)


        self.setSizePolicy( QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)

        self.setLayout(layout)

        self.show()

    def sizeHint(self):
        h = self.height()
        return QSize(h * PlayerWidget.aspect_ratio, h)

    def minimumSizeHint(self):
        return QSize()


    def startScoreFontSize(self):
        return self.height() * 0.2

    def resizeEvent(self, event):
        m = PlayerWidget.margin
        self.setContentsMargins( self.width() * m, 0, self.width() * m, 0)


    def set_lights(self, val):
        self.background = self.active_background if val else self.main_background
        self.update()

    def __buzz_hint(self):
        self.set_lights(True)
        time.sleep(0.25)
        self.set_lights(False)

    def buzz_hint(self):
        self.__buzz_hint_thread = Thread(
            target=self.__buzz_hint, name="buzz_hint"
        )
        self.__buzz_hint_thread.start()

    def update_score(self):
        score = self.player.score
        palette = self.score_label.palette()
        if score < 0:
            palette.setColor(QPalette.ColorRole.WindowText, RED)
        else:
            palette.setColor(QPalette.ColorRole.WindowText, WHITE)
        self.score_label.setPalette(palette)

        self.score_label.setText( f"{score:,}" )

    def run_lights(self):
        self.__light_thread = Thread(target=self.__lights, name="lights")
        self.__light_thread.start()

    def stop_lights(self):
        self.__light_thread = None
        self.set_lights(False)
        self.update()

    def __lights(self):
        for img in self.lights_backgrounds:
            self.background = img
            self.update()
            time.sleep(1.0)
            if self.__light_thread is None: # provide stopability
                return None

        self.set_lights(True)
        self.update()

    def mousePressEvent(self, event):
        if self.game.soliciting_player:
            self.game.get_dd_wager(self.player)
            return None

        self.game.adjust_score(self.player)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap( self.rect(), self.background )
        qp.end()

    def leaveEvent(self, event):
        if self.game.soliciting_player:
            self.set_lights(False)

    def enterEvent(self, event):
        if self.game.soliciting_player:
            self.set_lights(True)


class ScoreBoard(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)

        self.game = game

        # self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.player_widgets = []

        self.player_layout = QHBoxLayout()
        self.player_layout.addStretch()
        self.setLayout(self.player_layout)
        self.show()

    def minimumHeight(self):
        return 0.2 * self.width()

    def refresh_players(self):

        for pw in list(self.player_widgets): # copy list so we can remove elements
            if pw.player not in self.game.players:
                i = self.player_layout.indexOf(pw)
                self.player_layout.takeAt(i+1) # remove stretch
                self.player_layout.takeAt(i)
                self.player_widgets.remove(pw)
                pw.deleteLater()

        for (i,p) in enumerate(self.game.players):
            if not any(pw.player is p for pw in self.player_widgets):
                pw = PlayerWidget(self.game, p, self)
                self.player_layout.insertWidget(2*i+1, pw)
                self.player_layout.insertStretch(2*i+2)
                self.player_widgets.append(pw)

        self.update()

        # self.setLayout(self.player_layout)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap( self.rect(), QPixmap( resource_path("pedestal.png") ))
        qp.end()

    # def buzz_hint(self, player):
    #     for pw in self.player_widgets:
    #         if pw.player is player:
    #             pw.buzz_hint()

class Borders(object):
    def __init__(self, parent):
        super().__init__()
        self.left  = self.create_widget(parent, -1)
        self.right = self.create_widget(parent,  1)


    def __iter__(self):
        return iter([self.left, self.right])

    def create_widget(self, parent, d):
            return BorderWidget(parent, d)

    def __flash(self):
        self.lights(False)
        time.sleep(0.2)
        self.lights(True)
        time.sleep(0.2)
        self.lights(False)

    def flash(self):
        self.__flash_thread = Thread(
            target=self.__flash, name="flash"
        )
        self.__flash_thread.start()

    def lights(self, val):
        for b in self:
            b.lights(val)


class HostBorders(Borders):
    def __init__(self, parent):
        super().__init__(parent)
        self.__active_thread = None

    def create_widget(self, parent, d):
            return HostBorderWidget(parent, d)

    def __flash_hints(self, key):
        while self.__active_thread == current_thread():
            for b in self:
                b.show_hints(key)
            time.sleep(0.5)
            for b in self:
                b.hide_hints(key)
            time.sleep(0.5)

    def buzz_hint(self):
        self.__buzz_hint_thread = Thread(
            target=self.__buzz_hint, name="buzz_hint"
        )
        self.__buzz_hint_thread.start()


    def arrowhints(self, val):
        for b in self:
            b.colors = val
            b.update()

        if val:
            self.__active_thread = Thread(target=self.__flash_hints, args=('arrow',), name="arrow_hints")
            self.__active_thread.start()
        else:
            self.__active_thread = None
            for b in self:
                b.hide_hints('arrow')

    def spacehints(self, val):
        if val:
            self.__active_thread = Thread(target=self.__flash_hints, args=('space',), name="space_hints")
            self.__active_thread.start()
        else:
            self.__active_thread = None
            for b in self:
                b.hide_hints('space')

    def closeEvent(self, event):
        super().closeEvent(event)
        self.__active_hint = None


class BorderWidget(QWidget):
    def __init__(self, parent, d):
        super().__init__(parent)
        self.d = d
        self.__lit = False
        self.show()

    def lights(self, val):
        self.__lit = val
        self.update()

    def sizeHint(self):
        return QSize()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.__lit:
            qp.setBrush(QBrush(QColor("white")))
            qp.drawRect(self.rect())

class HostBorderWidget(BorderWidget):
    def __init__(self, parent, d):
        super().__init__(parent, d)
        self.layout = QVBoxLayout()
        self.hint_label = QLabel(self)

        self.layout.addWidget(self.hint_label)
        self.setLayout(self.layout)

        self.__hint_images = {
            'space' : QPixmap(resource_path("space.png")),
            'arrow' : QPixmap(resource_path(("right" if d==1 else "left") + "-arrow.png"))
            }

        self.colors = False
        self.show()

    def show_hints(self, key):
        self.hint_label.setPixmap(
            self.__hint_images[key].scaled( self.size() * 0.9,
                                        Qt.AspectRatioMode.KeepAspectRatio,
                                        transformMode=Qt.TransformationMode.SmoothTransformation
            )
        )

    def hide_hints(self, key):
        self.hint_label.setPixmap(QPixmap())

    def resizeEvent(self, event):
        self.hint_label.setMargin(self.width() * 0.05)

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter()
        qp.begin(self)
        if self.colors:
            qp.setBrush(QBrush(QColor("#ff0000" if self.d==1 else "#33cc33")))
            qp.drawRect(self.rect())






class DisplayWindow(QMainWindow):
    def __init__(self, game):

        super().__init__()
        self.game = game
        self.setWindowTitle("Host" if self.host() else "Board")

        colorpal = QPalette()
        colorpal.setColor(QPalette.ColorRole.Window, BLACK)
        self.setPalette(colorpal)



        self.welcome_widget = None
        self.question_widget = None


        self.board_widget = BoardWidget(game, self)
        self.scoreboard = ScoreBoard(game, self)

        self.borders = self.create_border_widget()

        self.main_layout = QVBoxLayout()

        self.board_layout = QHBoxLayout()
        self.board_layout.addWidget(self.borders.left, 1)
        self.board_layout.addWidget(self.board_widget, 20)
        self.board_layout.addWidget(self.borders.right, 1)
        self.main_layout.addLayout( self.board_layout, 7 )
        # self.main_layout.addWidget( self.lights_widget, 1 )
        self.main_layout.addWidget( self.scoreboard, 2)

        self.newWidget = QWidget(self)
        self.newWidget.setLayout(self.main_layout)

        self.welcome_widget = self.create_start_menu()

        self.final_window = None
        self.final_display = None


        self.setCentralWidget(self.newWidget)

        monitor = QGuiApplication.screens()[self.monitor()].geometry()

        self.setGeometry(monitor)

        if not DEBUG:
            self.showFullScreen()
        # self.resizeEvent(None)
        self.show()


    def host(self):
        return False

    def monitor(self):
        if DEBUG:
            return 0
        return 1

    def create_border_widget(self):
        return Borders(self)

    def create_start_menu(self):
        return QRWidget(self.game.buzzer_controller.host(), self)

    def create_question_widget(self, q):
        if q.dd:
            return DailyDoubleWidget(q, self)
        else:
            return QuestionWidget(q, self)

    def create_final_widget(self, q):
        return FinalJeopardyWidget(q, self)

    def resizeEvent(self, event):
        fullrect = self.rect()
        margins = QMargins(fullrect.width(), fullrect.height(), fullrect.width(), fullrect.height()) * 0.3
        if self.welcome_widget is not None:
            self.welcome_widget.setGeometry( fullrect - margins )
        if self.final_display is not None:
            self.final_display.setGeometry(fullrect)

    def show_welcome_widgets(self):
        self.welcome_widget.setVisible(True)
        self.welcome_widget.setDisabled(False)
        self.welcome_widget.restart()

    def hide_welcome_widgets(self):
        self.welcome_widget.setVisible(False)
        self.welcome_widget.setDisabled(True)

    def hide_question(self):
        self.board_widget.setVisible(True)
        self.board_layout.replaceWidget(self.question_widget, self.board_widget)
        self.question_widget.deleteLater()
        self.question_widget = None

    def load_question(self, q):
        self.question_widget = self.create_question_widget(q)
        self.board_widget.setVisible(False)
        self.board_layout.replaceWidget(self.board_widget, self.question_widget)

    def load_final(self, q):
        self.question_widget = self.create_final_widget(q)
        self.board_widget.setVisible(False)
        self.board_layout.replaceWidget(self.board_widget, self.question_widget)

    def load_final_judgement(self):
        self.final_display = FinalDisplay(self.game, self)
        self.final_window = self.final_display.answer_widget

    def closeEvent(self, event):
        super().closeEvent(event)
        self.game.close()

    def player_widget(self, player):
        for pw in self.scoreboard.player_widgets:
            if pw.player is player:
                return pw

    def remove_card(self, q):
        for label in self.board_widget.question_labels:
            if label.question is q:
                label.question = None

    def restart(self):
        self.hide_question()
        self.final_display.close()
        self.final_display = None
        self.board_widget.clear()
        self.show_welcome_widgets()
        self.scoreboard.refresh_players()

class HostDisplayWindow(DisplayWindow):
    def __init__(self, game):
        super().__init__(game)

    def host(self):
        return True

    def monitor(self):
        return 0


    def create_start_menu(self):
        return Welcome(self.game, self)

    def create_border_widget(self):
        return HostBorders(self)

    def create_question_widget(self, q):
        if q.dd:
            return HostDailyDoubleWidget(q, self)
        else:
            return HostQuestionWidget(q, self)

    def create_final_widget(self, q):
        return HostFinalJeopardyWidget(q, self)

    def keyPressEvent(self, event):
        self.game.keystroke_manager.call(event.key())
