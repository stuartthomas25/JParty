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


import os
from .retrieve import get_game, get_game_sum, get_random_game
from .game import game_params as gp
from .utils import resource_path, SongPlayer
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
ANSWERSECS = 5

FINALANSWERHEIGHT = 0.6

def updateUI(f):
    return f

def autofitsize(text, font, rect, start=None, stepsize=2):
    if start:
        font.setPointSize(start)

    size = font.pointSize()
    flags = Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter

    def fullrect(font, text=text, flags=flags):
        fm = QFontMetrics(font)
        return fm.boundingRect(rect, flags, text)

    newrect = fullrect(font)
    if not rect.contains(newrect):
        while size > 0:
            size -= stepsize
            font.setPointSize(size)
            newrect = fullrect(font)
            if rect.contains(newrect):
                return font.pointSize()

        logging.warn(f"Nothing fit! (text='{text}')")
        print(f"Nothing fit! (text='{text}')")

    return size

class DynamicLabel(QLabel):
    def __init__(self, text, initialSize, parent=None):
        super().__init__( text, parent )
        self.__initialSize = initialSize


        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    ### These three re-override QLabel's versions
    def sizeHint(self):
        return QSize()

    def initialSize(self):
        if callable(self.__initialSize):
            return self.__initialSize()
        else:
            return self.__initialSize


    def minimizeSizeHint(self):
        return QSize()

    def heightForWidth(self, w):
        return -1

    def resizeEvent(self, event):
        if self.size().height() == 0 or self.text() == "":
            return None

        fontsize = autofitsize(self.text(), self.font(), self.rect(), start=self.initialSize())
        font = self.font()
        font.setPointSize(fontsize)
        self.setFont(font)


class MyLabel(DynamicLabel):
    def __init__(self, text, initialSize, parent=None):
        super().__init__(text, initialSize, parent)
        self.setFont( QFont( "Helvetica" ) )
        self.font().setBold(True)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor("black"))
        shadow.setOffset(3)
        self.setGraphicsEffect(shadow)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
        self.setPalette(palette)

        self.show()


class QuestionLabel(QLabel):
    def __init__(self, text, rect, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: white;")
        self.setGeometry(QRect(rect))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.font = QFont("Helvetica")
        fontsize = autofitsize(text, self.font, rect, start=72)
        self.font.setPointSize(fontsize)
        self.setFont(self.font)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor("black"))
        shadow.setOffset(3)
        self.setGraphicsEffect(shadow)


class QuestionWidget(QWidget):
    def __init__(self, question, parent=None):
        super().__init__(parent)
        self.question = question

        self.responses_open = False

        # pheight = parent.geometry().height()
        # height = pheight * (1 - SCOREHEIGHT)
        # width = height / CELLRATIO
        self.resize(parent.size())
        # self.move(
        # self.parent().geometry().width() / 2 - self.parent().board_widget.geometry().width() / 2, 0
        # )
        alex = self.parent().alex

        if alex:
            anheight = ANSWERHEIGHT * self.size().height()
            self.qurect = self.rect().adjusted(
                QUMARGIN, QUMARGIN, -2 * QUMARGIN, -ANSWERHEIGHT * self.size().height(),
            )
            self.anrect = QRect(
                QUMARGIN,
                self.size().height() * (1 - ANSWERHEIGHT),
                self.size().width() - 2 * QUMARGIN,
                ANSWERHEIGHT * self.size().height(),
            )
            self.answer_label = QuestionLabel(question.answer, self.anrect, self)
            text = question.text

        else:
            self.qurect = self.rect().adjusted(
                QUMARGIN, QUMARGIN, -2 * QUMARGIN, -2 * QUMARGIN
            )
            self.anrect = None
            self.answer_label = None

            text = question.text.upper()

        self.question_label = QuestionLabel(text, self.qurect, self)

        self.show()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        qp.setBrush(FILLBRUSH)
        qp.drawRect(self.rect())
        # Show question
        if self.parent().alex:
            anheight = ANSWERHEIGHT * self.size().height()
            qp.drawLine(
                0,
                (1 - ANSWERHEIGHT) * self.size().height(),
                self.size().width(),
                (1 - ANSWERHEIGHT) * self.size().height(),
            )


class DailyDoubleWidget(QuestionWidget):
    def __init__(self, game, parent=None):
        super().__init__(game, parent)
        self.question_label.setVisible(False)
        if self.parent().alex:
            self.answer_label.setVisible(False)

        self.dd_label = QuestionLabel("DAILY<br/>DOUBLE!", self.qurect, self)
        self.dd_label.setFont(QFont("Helvetica", 140))
        self.dd_label.setVisible(True)
        self.update()

    def show_question(self):
        self.question_label.setVisible(True)
        if self.parent().alex:
            self.answer_label.setVisible(True)
        self.dd_label.setVisible(False)


class CardLabel(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)

        self.__margin = 0.1


        self.label = MyLabel(text, self.startFontSize, parent=self)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, BLUE)
        palette.setColor(QPalette.ColorRole.WindowText, WHITE)
        self.setPalette(palette)

        self.setAutoFillBackground(True)

    def startFontSize(self):
        return self.height() * 0.3

    def labelRect(self):
        wmargin = int(self.__margin * self.width())
        hmargin = int(self.__margin * self.height())
        return self.rect().adjusted(wmargin, hmargin, -wmargin, -hmargin)

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
        self.question = question
        if question is not None and not question.complete:
            moneytext = "$" + str(question.value)
        else:
            moneytext = ""
        super().__init__(moneytext)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.WindowText, YELLOW)
        self.setPalette(palette)

    def startFontSize(self):
        return self.height()*0.5

    def mousePressEvent(self, event):
        if self.question is not None and not self.question.complete:
            self.game.load_question(self.question)
            self.label.setText("")


class Board_Widget(QWidget):
    cell_ratio = 3/5
    rows = 6
    columns = 6
    def __init__(self, game, alex, parent=None):
        super().__init__(parent)
        self.game = game
        self.alex = alex
        self.__round = None

        self.responses_open = False

        self.questionwidget = None
        self.__completed_questions = []

        self.grid_layout = QGridLayout()

        self.resizeEvent(None)

        for x in range(Board_Widget.rows):
            self.grid_layout.setRowStretch(x, 1.)
        for y in range(Board_Widget.columns):
            self.grid_layout.setColumnStretch(y, 1.)

        for x in range(Board_Widget.rows):
            for y in range(Board_Widget.columns):

                if y == 0:
                    # Categories
                    # label = CardLabel(self.board.categories[x])
                    label = CardLabel("")
                    self.grid_layout.addWidget(label, 0, x)

                else:
                    # Questions
                    if self.__round is not None:
                        q = self.__round.get_question(x,y-1)
                    else:
                        q = None

                    label = QuestionCard(game, q)
                    self.grid_layout.addWidget(label, y, x)


        self.setLayout(self.grid_layout)

        self.show()

    def resizeEvent(self, event):
        self.grid_layout.setSpacing(self.width() // 150)

    # def paintEvent(self, event):
    #     h = self.geometry().height()
    #     w = self.geometry().width()
    #     qp = QPainter()
    #     qp.begin(self)
    #     qp.setBrush(QBrush(YELLOW))
    #     qp.drawRect(self.rect())

    # def minimumSizeHint(self):
    #     return QSize(self.geometry().width(), 900)

    # @updateUI
    # def resizeEvent(self, event):
    #     print(self.geometry().height())
    #     print(self.parent().geometry().height())
    #     parent = self.parent()
    #     pheight = parent.geometry().height()
    #     height = pheight * (1 - SCOREHEIGHT)
    #     width = height / CELLRATIO
    #     self.resize(width + BORDERWIDTH, height)
    #     print("RESIZE!")


    @property
    def board(self):
        return self.game.current_round

    # def paintEvent(self, event):
    #     return None
    #     qp = QPainter()
    #     qp.begin(self)
    #     qp.setBrush(FILLBRUSH)
    #     parent = self.parent()
    #     pheight = parent.geometry().height()
    #     height = pheight * (1 - SCOREHEIGHT)
    #     width = height / CELLRATIO
    #     if not self.board.final:
    #         # Normal board
    #         for x in range(self.board.size[0]):
    #             for y in range(-1, self.board.size[1]):
    #                 rel_pos = (
    #                     x * self.cellsize[0] + BORDERWIDTH / 2,
    #                     (y + 1) * self.cellsize[1],
    #                 )
    #                 cell = (x, y)
    #                 qp.setPen(BORDERPEN)
    #                 qp.setBrush(FILLBRUSH)
    #                 cell_rect = QRectF(*rel_pos, *self.cellsize)
    #                 text_rect = QRectF(cell_rect)
    #                 text_rect.setX(cell_rect.x() + TEXTPADDING)
    #                 text_rect.setWidth(cell_rect.width() - 2 * TEXTPADDING)
    #                 qp.drawRect(cell_rect)
    #                 if y == -1:
    #                     # Categories
    #                     qp.setPen(CATPEN)
    #                     qp.setFont(CATFONT)
    #                     qp.drawText(
    #                         text_rect,
    #                         Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
    #                         self.board.categories[x],
    #                     )
    #                 else:
    #                     # Questions
    #                     q = self.board.get_question(*cell)
    #                     if not q in self.game.completed_questions:
    #                         qp.setPen(MONPEN)
    #                         qp.setFont(MONFONT)
    #                         if not self.board.dj:
    #                             monies = gp.money1
    #                         else:
    #                             monies = gp.money2
    #                         qp.drawText(
    #                             text_rect,
    #                             Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
    #                             "$" + str(q.value),
    #                         )
    #     else:
    #         # Final jeopardy
    #         qp.setBrush(FILLBRUSH)
    #         qp.drawRect(self.rect())
    #         qp.setPen(CATPEN)
    #         qp.setFont(QUFONT)

    #         qurect = self.rect().adjusted(
    #             QUMARGIN, QUMARGIN, -2 * QUMARGIN, -2 * QUMARGIN
    #         )

    #         qp.drawText(
    #             qurect,
    #             Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
    #             self.board.categories[0],
    #         )

    @updateUI
    def load_question(self, q):
        if q.dd:
            self.questionwidget = DailyDoubleWidget(q, self)
        else:
            logging.info("Question widget!")
            self.questionwidget = QuestionWidget(q, self)

    @updateUI
    def hide_question(self):
        delete(self.questionwidget)


class PlayerWidget(QWidget):
    aspect_ratio = 0.732
    name_aspect_ratio = 1.3422
    margin = 0.05
    def __init__(self, game, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.game = game
        self.__buzz_hint_thread = None

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

        self.background_img = QPixmap( resource_path("player.png") )

        self.highlighted = False

        layout = QVBoxLayout()
        layout.addStretch(4)
        layout.addWidget(self.score_label, 11)
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
        self.background_img = QPixmap( resource_path("player_active.png") )
        self.update()
        time.sleep(0.25)
        self.background_img = QPixmap( resource_path("player.png") )
        self.update()

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

    def mousePressEvent(self, event):
        print(self.player.name)
        self.game.adjust_score(self.player)
        self.update_score()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap( self.rect(), self.background_img )


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


    def resizeEvent(self, event):
        pass
        # spacing  = int( self.width() / (len(self.game.players) + 1) * 0.3 )
        # self.player_layout.setContentsMargins( spacing, 0, spacing, 0)
        # self.player_layout.setSpacing( spacing )

    def minimumHeight(self):
        return 0.2 * self.width()

    def refresh_players(self):
        for pw in self.player_widgets:
            if pw.player not in self.game.players:
                print("remove player")
                self.player_layout.removeWidget(pw)
                self.player_widgets.remove(pw)
                delete(pw)

        for (i,p) in enumerate(self.game.players):
            if not any(pw.player is p for pw in self.player_widgets):
                print("add player")
                pw = PlayerWidget(self.game, p, self)
                self.player_layout.insertWidget(2*i+1, pw)
                self.player_layout.insertStretch(2*i+2)
                self.player_widgets.append(pw)

        # self.setLayout(self.player_layout)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap( self.rect(), QPixmap( resource_path("pedestal.png") ))

    def buzz_hint(self, player):
        for pw in self.player_widgets:
            if pw.player is player:
                pw.buzz_hint()


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


class Borders(object):
    def __init__(self, parent):
        super().__init__()
        self.left  = BorderWidget(parent, -1)
        self.right = BorderWidget(parent,  1)

    def __iter__(self):
        return iter([self.left, self.right])


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
    def __init__(self, parent=None, d=1):
        super().__init__(parent)
        self.d = d

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.hint_label = QLabel(self)

        # icon_size = 64
        # self.icon_label.setPixmap(
        #     QPixmap(resource_path("space.png")).scaled(
        #         icon_size,
        #         icon_size,
        #         transformMode=Qt.TransformationMode.SmoothTransformation,
        #     )
        # )
        #
        self.space_image = QPixmap(resource_path("space.png"))

        self.layout.addWidget(self.hint_label)
        self.setLayout(self.layout)

        self.show()

    def lights(self, val):
        color = val if WHITE else BLACK
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, color)
        self.setPalette(palette)

    def arrowhints(self, val):
        pass

    def spacehints(self, val):
        if val:
            self.hint_label.setPixmap(
                self.space_image.scaled( self.size(),
                                         Qt.AspectRatioMode.KeepAspectRatio,
                                         transformMode=Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            self.hint_label.setPixmap(QPixmap())

    def sizeHint(self):
        return QSize()


class DisplayWindow(QMainWindow):
    def __init__(self, game, alex=True, monitor=0):
        super().__init__()
        self.alex = alex
        self.game = game
        self.setWindowTitle("Host" if alex else "Board")

        colorpal = QPalette()
        colorpal.setColor(QPalette.ColorRole.Window, BLACK)
        self.setPalette(colorpal)

        # monitor = QDesktopWidget().screenGeometry(monitor)
        if DEBUG:
            if len(QGuiApplication.screens()) == 1:
                monitor = 0

        monitor = QGuiApplication.screens()[monitor].geometry()

        # self.move(monitor.left(), monitor.top())  # move to monitor 0
        self.welcome_widget = None
        self.qrwidget = None

        # self.lights_widget = LightsWidget(self)
        self.showFullScreen()

        self.board_widget = Board_Widget(game, alex, self)
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


        if alex:
            self.welcome_widget = Welcome(game, self)
            self.qrwidget = None

        self.setCentralWidget(self.newWidget)
        self.resizeEvent(None)
        self.show()


    def resizeEvent(self, event):
        if self.welcome_widget is not None:
            fullrect = self.geometry()
            margins = QMargins(fullrect.width(), fullrect.height(), fullrect.width(), fullrect.height()) * 0.3
            self.welcome_widget.setGeometry( fullrect - margins )

    # def resizeEvent(self, event):
    #     main_layout = self.centralWidget().layout()
    #     main_layout.setStretchFactor( self.board_widget,2 )
    #     self.centralWidget().setLayout(main_layout)

    def hide_question(self):
        self.board_widget.hide_question()

    def keyPressEvent(self, event):
        if self.game is not None:
            self.game.keystroke_manager.call(event.key())

    def load_question(self, q):
        logging.info("DC load_question")
        self.board_widget.load_question(q)


class Welcome(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.valid_game = False
        self.gamedata = None
        self.song_player = SongPlayer()

        if not DEBUG:
            self.song_player.play(repeat=True)
        else:
            self.song_player = None



        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main_layout.setContentsMargins(20,20,20,20)

        self.icon_label = QLabel(self)
        icon_size = 84
        icon = QPixmap(resource_path("icon.png"))
        self.icon_label.setPixmap(
            icon.scaled(
                icon_size,
                icon_size,
                transformMode=Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.icon_label.resize(icon_size, icon_size)

        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_layout.addWidget(self.icon_label)
        icon_layout.addStretch()

        main_layout.addLayout(icon_layout)


        self.title_font = QFont()
        self.title_font.setPointSize(24)
        self.title_font.setBold(True)

        self.title_label = QLabel("JParty!")
        self.title_label.setFont(self.title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main_layout.addWidget(self.title_label)

        self.version_label = QLabel(f"version {version}\nCopyright © Stuart Thomas 2022\nDistributed under the GNU General Public License (v3)")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.version_label.setStyleSheet("QLabel { color : grey}")

        self.version_font = QFont()
        self.version_font.setPointSize(10)
        self.version_label.setFont(self.version_font)
        main_layout.addWidget(self.version_label)

        select_layout = QHBoxLayout()

        template_url = "https://docs.google.com/spreadsheets/d/1_vBBsWn-EVc7npamLnOKHs34Mc2iAmd9hOGSzxHQX0Y/edit#gid=0"
        gameid_text = f"Game ID:<br>(from J-Archive URL) <br>or <a href=\"{template_url}\">GSheet ID for custom game</a>"
        gameid_label = QLabel(gameid_text, self)
        gameid_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        gameid_label.setOpenExternalLinks(True)
        select_layout.addWidget(gameid_label)

        self.textbox = QLineEdit(self)
        self.textbox.resize(100, 40)
        self.textbox.textChanged.connect(self.show_summary)
        f = self.textbox.font()
        f.setPointSize(30)  # sets the size to 27
        self.textbox.setFont(f)
        select_layout.addWidget(self.textbox)

        button_layout = QVBoxLayout()
        self.start_button = QPushButton("Start!", self)
        self.start_button.setToolTip("Start Game")
        self.start_button.clicked.connect(self.init_game)
        button_layout.addWidget(self.start_button)

        self.rand_button = QPushButton("Random", self)
        self.rand_button.setToolTip("Get a Random Game")
        self.rand_button.clicked.connect(self.random)
        button_layout.addWidget(self.rand_button)
        select_layout.addLayout(button_layout)

        main_layout.addLayout(select_layout)

        self.summary_label = QLabel("", self)
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.summary_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        main_layout.addWidget(self.summary_label, 1)

        self.help_button = QPushButton("Show help", self)
        self.help_button.clicked.connect(self.show_help)
        help_button_layout = QHBoxLayout()
        help_button_layout.addStretch()
        help_button_layout.addWidget(self.help_button)
        help_button_layout.addStretch()

        main_layout.addLayout(help_button_layout)
        main_layout.addStretch()
        # main_layout.addWidget(self.help_button, 1)

        self.setLayout(main_layout)


        # qtRectangle = self.geometry()
        # centerPoint = self.parent().geometry().center()
        # qtRectangle.moveCenter(centerPoint)
        # self.move(qtRectangle.topLeft())

        if DEBUG:
            self.textbox.setText(str(2534))  # EDIT

        ### FOR TESTING

        # self.socket_controller.connected_players = [
        # Player("Stuart", None),
        # ]
        # self.socket_controller.connected_players[0].token = bytes.fromhex(
        # "6ab3a010ce36cc5c62e3e8f219c9be"
        # )
        # self.init_game()


        self.show()



    def show_help(self):
        logging.info("Showing help")
        msgbox = QMessageBox(
            QMessageBox.Icon.NoIcon,
            "JParty Help",
            helpmsg,
            QMessageBox.StandardButton.Ok,
            self,
        )
        msgbox.exec()
        # self.initUI()

        # if os.path.exists(".bkup"):
        #     logging.info("backup")
        #     self.run_game(pickle.load(open(".bkup", "rb")))

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        qp.setBrush(FILLBRUSH)
        qp.drawRect(self.rect())

    # def show_overlay(self):
    #     if not DEBUG:
    #         self.host_overlay = HostOverlay(self.socket_controller.host())
    #         self.windowHandle().setScreen(QApplication.instance().screens()[1])
    #         self.host_overlay.showNormal()


    def _random(self):
        complete = False
        while not complete:
            game_id = get_random_game()
            logging.info(f"GAMEID {game_id}")
            complete = all(b.complete for b in get_game(game_id).rounds)


        self.textbox.setText(str(game_id))
        self.textbox.show()

    def random(self, checked):
        self.summary_label.setText("Loading...")
        t = Thread(target=self._random)
        t.start()

    @updateUI
    def _show_summary(self):
        game_id = self.textbox.text()
        try:
            self.gamedata = get_game(game_id)
            if all(b.complete for b in self.gamedata.rounds):
                self.summary_label.setText(self.gamedata.date + "\n" + self.gamedata.comments)
                self.valid_game = True
            else:
                self.summary_label.setText("Game has blank questions")
                self.valid_game = False
        except ValueError as e:
            self.summary_label.setText("invalid game id")
            self.valid_game = False
        self.check_start()

    def show_summary(self, text=None):
        logging.info("show sum")
        self.summary_label.setText("Loading...")
        t = Thread(target=self._show_summary)
        t.start()

        self.check_start()


    def check_start(self):
        if self.startable():
            self.start_button.setEnabled(True)
        else:
            self.start_button.setEnabled(False)

    def startable(self):
        if DEBUG:
            return True
        return (
            self.valid_game
            and len(self.socket_controller.connected_players) > 0
            and len(QApplication.instance().screens()) > 1
        )

    def init_game(self):
        try:
            game_id = self.textbox.text()
            if type(game_id) == str:
                get_game(game_id)

        except ValueError as e:
            error_dialog = QErrorMessage()
            error_dialog.showMessage("Invalid game ID - change sharing permissions & try again")
            return False

        self.gamedata = get_game(game_id)
        game = Game(self.gamedata)
        game.welcome_window = self
        game.players = self.socket_controller.connected_players
        if DEBUG:
            game.players = [
                Player(f"Stuart", None),
                Player(f"Maddie", None),
                Player(f"Koda", None)
            ]

        self.run_game(game)

    def run_game(self, game):
        if self.song_player:
            self.song_player.stop()
        self.socket_controller.game = game
        game.buzzer_controller = self.socket_controller


        if not DEBUG:
            self.host_overlay.close()
        self.show_board(game)

    def show_board(self, game):
        game.alex_window = DisplayWindow(alex=True, monitor=0)
        game.main_window = DisplayWindow(alex=False, monitor=1)
        game.dc += game.alex_window
        game.dc += game.main_window

        self.start_button.setEnabled(False)

    def restart(self):
        self.player_view.close()
        self.player_view = PlayerView(self.rect() - QMargins(0, 210, 0, 0), parent=self)
        # self.show_overlay()
        QTimer.singleShot(500, self.show_overlay)

        self.start_button.setEnabled(False)

    @updateUI
    def new_player(self, player):
        PlayerView.new_player(player)
        self.check_start()
        # label = self.player_labels[len(self.socket_controller.connected_players) - 1]
        # label.setText(player.name)
        # label.setFixedWidth(LABELWIDTH)
        # label.move(label.pos() + QPoint((MOVIEWIDTH - LABELWIDTH)/2,0))
        # label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.check_start()

    @updateUI
    def buzz_hint(self, i_player):
        player = self.socket_controller.connected_players[i_player]
        PlayerView.buzz_hint(player)
        # for l in self.player_labels:
        # if player.name == l.text():
        # l.setStyleSheet("QLabel { background-color : grey}")
        # def return_to_default(label=l, widget=self):
        # l.setStyleSheet("QLabel { background-color : none}")
        # self.update()

        # t = threading.Timer(0.1, return_to_default)
        # t.start()

        # break

    def closeEvent(self, event):
        if os.path.exists(".bkup"):
            os.remove(".bkup")
        QApplication.quit()


class PlayerLabel(QLabel):
    loading_movie = None

    def __init__(self, fontsize, parent=None):
        super().__init__(parent)
        self.fontsize = fontsize

        cls = type(self)
        if not cls.loading_movie:
            cls.loading_movie = QMovie(resource_path("loading.gif"))
            cls.loading_movie.setScaledSize(QSize(MOVIEWIDTH, MOVIEWIDTH))
            cls.loading_movie.start()
        # self.player_heading.setGeometry(0, 140, self.rect().width(), 50)
        # self.player_heading.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        f = self.font()
        f.setPointSize(self.fontsize)
        self.setFont(f)
        self.setAutoFillBackground(True)

        self.setMovie(cls.loading_movie)

        self.blink_timer = None

    def buzz_hint(self):
        self.setStyleSheet("QLabel { background-color : grey}")
        self.blink_timer = QTimer()
        # self.blink_timer.moveToThread(QApplication.instance().thread())
        self.blink_timer.timeout.connect(self._buzz_hint_callback)
        self.blink_timer.start(100)

    def _buzz_hint_callback(self):
        self.setStyleSheet("QLabel { background-color : none}")
class HostOverlay(QWidget):
    def __init__(self, host):
        QMainWindow.__init__(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        if DEBUG:
            screen = QGuiApplication.screens()[0]
        else:
            screen = QGuiApplication.screens()[1]

        screen_width = screen.size().width()
        display_width = int(0.7 * screen_width)
        display_height = int(0.2 * display_width)
        font_size = int(0.06 * display_width)

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LayoutDirection.LeftToRight,
                Qt.AlignmentFlag.AlignCenter,
                QSize(display_width, display_height),
                screen.geometry(),
            )
        )

        font = QFont()
        font.setPointSize(font_size)


        url = "http://" + host

        self.label = QLabel(url, self)
        self.label.setGeometry(
            self.rect() - QMargins(0, 0, 0, self.rect().height() // 2)
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(font)

        self.qrlabel = QLabel(self)
        self.qrlabel.setPixmap(
            qrcode.make(url,
                        image_factory=Image,
                        box_size=self.label.rect().height()//30).pixmap())

        self.qrlabel.setGeometry( self.label.rect())
        self.qrlabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        #     self.label.geometry().right(),
        #     self.label.geometry().y(),
        #     self.label.geometry().height(),
        #     self.label.geometry().height()
        # ))


        self.show()

    def closeEvent(self, event):
        event.accept()
