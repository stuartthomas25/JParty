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
)
from PyQt6.sip import delete
from .version import version
import qrcode


from .welcome_widget import Welcome, QRWidget
import os
from .retrieve import get_game, get_game_sum, get_random_game
from .game import game_params as gp
from .utils import resource_path, SongPlayer, add_shadow, DynamicLabel
from .constants import DEBUG
from .helpmsg import helpmsg
import time
from threading import Thread, active_count
import re
import logging
from base64 import urlsafe_b64decode

margin = 50
n = 8  # even integer
FONTSIZE = 10

BLUE = QColor("#1010a1")
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
        self.setFont( QFont( "Helvetica" ) )
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
        self.question_label = MyLabel(question.text, self.startFontSize, self)
        self.main_layout.addWidget(self.question_label)
        self.setLayout(self.main_layout)

        self.setPalette(CARDPAL)
        self.show()

    def startFontSize(self):
        return self.width() * 0.05


class HostQuestionWidget(QuestionWidget):
    def __init__(self, question, parent=None):
        super().__init__(question, parent)

        self.main_layout.setStretchFactor(self.question_label, 6)
        self.answer_label = MyLabel(question.answer, self.startFontSize, self)
        self.main_layout.addWidget(self.answer_label, 1)
        self.setLayout(self.main_layout)


    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        line_y = self.answer_label.geometry().top()
        qp.drawLine(0, line_y, self.width(), line_y)


class DailyDoubleWidget(QuestionWidget):
    def __init__(self, game, parent=None):
        super().__init__(game, parent)
        self.question_label.setVisible(False)
        if self.parent().alex:
            self.answer_label.setVisible(False)

        self.dd_label = QuestionLabel("DAILY<br/>DOUBLE!", self.qurect, self)
        self.dd_label.setFont(QFont("Helvetica", 140))
        self.dd_label.setVisible(True)

    def show_question(self):
        self.question_label.setVisible(True)
        if self.parent().alex:
            self.answer_label.setVisible(True)
        self.dd_label.setVisible(False)


class CardLabel(QWidget):
    margin = 0.1
    def __init__(self, text, parent=None):
        super().__init__(parent)

        self.label = MyLabel(text, self.startFontSize, parent=self)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, BLUE)
        palette.setColor(QPalette.ColorRole.WindowText, WHITE)
        self.setPalette(palette)

        self.setAutoFillBackground(True)

    def startFontSize(self):
        return self.height() * 0.3

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
        return self.height()*0.5


class HostQuestionCard(QuestionCard):
    def mousePressEvent(self, event):
        if self.question is not None and not self.question.complete:
            self.game.load_question(self.question)
            self.label.setText("")


class BoardWidget(QWidget):
    cell_ratio = 3/5
    rows = 6
    columns = 6

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.__round = None

        self.responses_open = False

        self.questionwidget = None
        self.__completed_questions = []

        self.grid_layout = QGridLayout()

        self.resizeEvent(None)

        for x in range(BoardWidget.rows):
            self.grid_layout.setRowStretch(x, 1.)
        for y in range(BoardWidget.columns):
            self.grid_layout.setColumnStretch(y, 1.)

        for x in range(BoardWidget.rows):
            for y in range(BoardWidget.columns):

                if y == 0:
                    label = CardLabel("")
                    self.grid_layout.addWidget(label, 0, x)

                else:
                    if self.parent().host():
                        label = HostQuestionCard(game, None)
                    else:
                        label = QuestionCard(game, None)
                    self.grid_layout.addWidget(label, y, x)


        self.setLayout(self.grid_layout)

        self.show()

    def load_round(self, round):
        gl = self.grid_layout
        for x in range(BoardWidget.rows):
            for y in range(BoardWidget.columns):
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

class MainBoardWidget(BoardWidget):
    pass

class HostBoardWidget(BoardWidget):
    def load_question(self, q):
        if q.dd:
            self.questionwidget = DailyDoubleWidget(q, self)
        else:
            self.questionwidget = HostQuestionWidget(q, self)


class PlayerWidget(QWidget):
    aspect_ratio = 0.732
    name_aspect_ratio = 1.3422
    margin = 0.05

    def __init__(self, game, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.game = game
        self.__buzz_hint_thread = None
        self.__light_thread = None

        if player.name[:21] == 'data:image/png;base64':
            i = QImage()
            i.loadFromData(urlsafe_b64decode(self.player.name[22:]), "PNG")
            self.signature = QPixmap.fromImage(i)
            self.name_label = DynamicLabel("", 0, self)
        else:

            self.name_label = MyLabel(player.name, self.startNameFontSize, self)
            self.signature = None

        self.score_label = MyLabel("$0", self.startScoreFontSize, self)

        self.resizeEvent(None)
        self.update_score()


        self.main_background = QPixmap( resource_path("player.png") )
        self.active_background= QPixmap( resource_path("player_active.png") )
        self.lights_backgrounds = [QPixmap( resource_path(f"player_lights{i}.png") ) for i in range(1,6)]
        self.background = self.main_background

        self.highlighted = False

        layout = QVBoxLayout()
        layout.addStretch(5)
        layout.addWidget(self.score_label, 10)
        layout.addStretch(9)
        layout.addWidget(self.name_label, 32)
        layout.addStretch(10)
        layout.setContentsMargins( 0, 0, 0, 0)


        self.setSizePolicy( QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)

        self.setLayout(layout)

        self.show()

    def sizeHint(self):
        h = self.height()
        return QSize(h * PlayerWidget.aspect_ratio, h)

    def minimumSizeHint(self):
        return QSize()

    def startNameFontSize(self):
        return self.height() * 0.2

    def startScoreFontSize(self):
        return self.height() * 0.2

    def resizeEvent(self, event):
        if self.size().height() == 0:
            return None

        m = PlayerWidget.margin
        self.setContentsMargins( self.width() * m, 0, self.width() * m, 0)

        ## Add signture
        if self.signature is not None:
            self.name_label.setPixmap(
                self.signature.scaled(
                    self.name_label.width(), self.name_label.width() / PlayerWidget.name_aspect_ratio,
                    transformMode=Qt.TransformationMode.SmoothTransformation,
                )
            )


    def __buzz_hint(self):
        self.background = self.active_background
        self.update()
        time.sleep(0.25)
        self.background = self.main_background
        self.update()

    def buzz_hint(self):
        self.__buzz_hint_thread = Thread(
            target=self.__buzz_hint, name="buzz_hint"
        )
        self.__buzz_hint_thread.start()

    def update_score(self):
        logging.info("update_score")
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
        self.background = self.main_background
        self.update()

    def __lights(self):
        for img in self.lights_backgrounds:
            self.background = img
            self.update()
            time.sleep(1.0)
            if self.__light_thread is None: # provide stopability
                return None

        self.background = self.active_background
        self.update()


    def mousePressEvent(self, event):
        self.game.adjust_score(self.player)
        self.update_score()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap( self.rect(), self.background )
        qp.end()


class ScoreBoard(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)

        self.game = game

        # self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.player_widgets = []

        self.player_layout = QHBoxLayout()
        self.player_layout.setContentsMargins(0,0,0,0)
        self.player_layout.addStretch()
        self.setLayout(self.player_layout)
        self.show()

    def minimumHeight(self):
        return 0.2 * self.width()

    def refresh_players(self):
        for pw in self.player_widgets:
            if pw.player not in self.game.players:
                self.player_layout.removeWidget(pw)
                self.player_widgets.remove(pw)
                delete(pw)

        for (i,p) in enumerate(self.game.players):
            if not any(pw.player is p for pw in self.player_widgets):
                pw = PlayerWidget(self.game, p, self)
                self.player_layout.insertWidget(2*i+1, pw)
                self.player_layout.insertStretch(2*i+2)
                self.player_widgets.append(pw)

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


class FinalAnswerWidget(QWidget):
    def __init__(self, game, parent=None):
        super().__init__()
        self.game = game
        self.__margin = 50
        self.winner = None

        if parent.alex:
            self.setGeometry(
                parent.board_widget.x(),
                self.__margin,
                parent.board_widget.width(),
                parent.height() * FINALANSWERHEIGHT,
            )

        else:
            self.setGeometry(
                0, self.__margin, parent.width(), parent.height() * FINALANSWERHEIGHT,
            )
        self.info_level = 0

        self.__light_level = 0
        self.__light_thread = None

        self.show()

    def paintEvent(self, event):
        h = self.geometry().height()
        w = self.geometry().width()
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(FILLBRUSH)
        qp.drawRect(self.rect())

        p = self.game.answering_player
        margin = self.__margin

        qp.setPen(SCOREPEN)
        qp.setFont(SCOREFONT)

        if self.winner:
            winnerrect = QRectF(0, NAMEHEIGHT + 2 * margin, w, 2 * NAMEHEIGHT)
            qp.drawText(
                winnerrect,
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                f"{self.winner.name} is the winner!",
            )
            return

        namerect = QRectF(0, margin, w, NAMEHEIGHT)
        qp.drawText(
            namerect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter, p.name
        )

        if self.info_level > 0:
            answerrect = QRectF(0, NAMEHEIGHT + 2 * margin, w, 2 * NAMEHEIGHT)
            finalanswer = (
                p.finalanswer
                if len(p.finalanswer.replace(" ", "")) > 0
                else "_________"
            )
            qp.drawText(
                answerrect,
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                finalanswer,
            )

        if self.info_level > 1:
            wagerrect = QRectF(0, h - NAMEHEIGHT - margin, w, NAMEHEIGHT)
            qp.drawText(
                wagerrect,
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                f"{p.wager:,}",
            )
        qp.end()


class Borders(object):
    def __init__(self, parent):
        super().__init__()
        if parent.host():
            self.left  = HostBorderWidget(parent, -1)
            self.right = HostBorderWidget(parent,  1)
        else:
            self.left  = BorderWidget(parent, -1)
            self.right = BorderWidget(parent,  1)

    def __iter__(self):
        return iter([self.left, self.right])


    def flash(self):
        self.lights(False)
        time.sleep(0.2)
        self.lights(True)
        time.sleep(0.2)
        self.lights(False)

    def lights(self, val):
        for b in self:
            b.lights(val)

    def arrowhints(self, val):
        for b in self:
            b.arrowhints(val)

    def spacehints(self, val):
        for b in self:
            b.spacehints(val)


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

    def arrowhints(self, val):
        pass

    def spacehints(self, val):
        pass


class HostBorderWidget(BorderWidget):
    def __init__(self, parent, d):
        super().__init__(parent, d)
        self.layout = QVBoxLayout()
        self.hint_label = QLabel(self)

        self.layout.setContentsMargins(0,0,0,0)
        self.layout.addWidget(self.hint_label)
        self.setLayout(self.layout)

        self.__space_image = QPixmap(resource_path("space.png"))
        self.__arrow_image = QPixmap(resource_path(("right" if d==1 else "left") + "-arrow.png"))
        self.__arrow_lit = False
        self.show()

    def arrowhints(self, val):
        logging.info(f"ARROWHINTS {val}")
        self.__arrow_lit = val
        if val:
            self.hint_label.setMargin(self.width() * 0.05)
            self.hint_label.setPixmap(
                self.__arrow_image.scaled( self.size() * 0.9,
                                         Qt.AspectRatioMode.KeepAspectRatio,
                                         transformMode=Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            self.hint_label.setPixmap(QPixmap())

    def spacehints(self, val):
        if val:
            self.hint_label.setPixmap(
                self.__space_image.scaled( self.size() * 0.9,
                                         Qt.AspectRatioMode.KeepAspectRatio,
                                         transformMode=Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            self.hint_label.setPixmap(QPixmap())

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter()
        qp.begin(self)
        if self.__arrow_lit:
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

        if DEBUG:
            if len(QGuiApplication.screens()) == 1:
                monitor = 0

        monitor = QGuiApplication.screens()[self.monitor()].geometry()

        self.welcome_widget = None
        self.question_widget = None

        # self.lights_widget = LightsWidget(self)
        # self.showFullScreen()

        self.board_widget = BoardWidget(game, self)
        self.scoreboard = ScoreBoard(game, self)
        # self.finalanswerwindow = FinalAnswerWidget(game)
        # self.finalanswerwindow.setVisible(False)

        self.borders = Borders(self)

        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0.)
        self.main_layout.setContentsMargins(0., 0., 0., 0.)

        self.board_layout = QHBoxLayout()
        self.board_layout.setContentsMargins(0., 0., 0., 0.)
        self.board_layout.addWidget(self.borders.left, 1)
        self.board_layout.addWidget(self.board_widget, 20)
        self.board_layout.addWidget(self.borders.right, 1)
        self.main_layout.addLayout( self.board_layout, 7 )
        # self.main_layout.addWidget( self.lights_widget, 1 )
        self.main_layout.addWidget( self.scoreboard, 2)

        self.newWidget = QWidget(self)
        self.newWidget.setLayout(self.main_layout)

        self.welcome_widget = self.create_start_menu()

        self.setCentralWidget(self.newWidget)
        self.resizeEvent(None)
        self.show()

    def host(self):
        return False

    def monitor(self):
        return 0

    def create_start_menu(self):
        return QRWidget(self.game.socket_controller.host(), self)

    def create_question_widget(self, q):
        if q.dd:
            self.questionwidget = DailyDoubleWidget(q, self)
        else:
            self.questionwidget = QuestionWidget(q, self)

    def resizeEvent(self, event):
        fullrect = self.rect()
        margins = QMargins(fullrect.width(), fullrect.height(), fullrect.width(), fullrect.height()) * 0.3
        if self.welcome_widget is not None:
            self.welcome_widget.setGeometry( fullrect - margins )

    def hide_welcome_widgets(self):
        if self.welcome_widget is not None:
            self.welcome_widget.setVisible(False)
            self.welcome_widget.setDisabled(True)

    def hide_question(self):
        self.board_widget.setVisible(True)
        self.board_widget.setDisabled(False)
        self.board_layout.replaceWidget(self.question_widget, self.board_widget)
        delete(self.question_widget)

    def load_question(self, q):
        self.question_widget = self.create_question_widget(q)
        self.board_widget.setVisible(False)
        self.board_widget.setDisabled(True)
        self.board_layout.replaceWidget(self.board_widget, self.question_widget)

    def closeEvent(self, event):
        self.game.close()

    def player_widget(self, player):
        for pw in self.scoreboard.player_widgets:
            if pw.player is player:
                return pw

class HostDisplayWindow(DisplayWindow):
    def __init__(self, game):
        super().__init__(game)

    def host(self):
        return True

    def monitor(self):
        logging.warn("Using one monitor!")
        return 0

    def create_start_menu(self):
        return Welcome(self.game, self)


    def create_question_widget(self, q):
        if q.dd:
            self.questionwidget = DailyDoubleWidget(q, self)
        else:
            self.questionwidget = HostQuestionWidget(q, self)

    def keyPressEvent(self, event):
        self.game.keystroke_manager.call(event.key())
